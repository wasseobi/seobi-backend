"""메시지 처리 서비스."""
from app.dao.message_dao import MessageDAO
from app.services.session_service import SessionService
from app.models import Session
from app.models.db import db
from app.utils.openai_client import get_openai_client, get_completion
from app.langgraph.graph import build_graph as langgraph_builder
from app.langgraph.executor import create_agent_executor
from app.langgraph.utils.message_formatter import format_message_content
from langchain.schema import HumanMessage, AIMessage
from langchain_core.messages import BaseMessage, ToolMessage
from typing import List, Dict, Any, Generator, Union
from datetime import datetime
import uuid
import json
import logging


class MessageService:
    def __init__(self):
        self.dao = MessageDAO()
        self.session_service = SessionService()
        self.agent = create_agent_executor()
        graph = langgraph_builder()
        self.graph = graph.compile()

    def _serialize_message(self, message: Any) -> Dict[str, Any]:
        """Serialize message data for API response"""
        return {
            'id': str(message.id),
            'session_id': str(message.session_id),
            'user_id': str(message.user_id),
            'content': message.content,
            'role': message.role,
            'timestamp': message.timestamp.isoformat() if message.timestamp else None,
            'vector': message.vector.tolist() if message.vector is not None else None,
            'metadata': message.message_metadata
        }

    def get_all_messages(self) -> List[Dict]:
        """Get all messages"""
        messages = self.dao.get_all_messages()
        return [self._serialize_message(msg) for msg in messages]

    def get_message(self, message_id: uuid.UUID) -> Dict:
        """Get a message by ID"""
        message = self.dao.get_message_by_id(message_id)
        if not message:
            raise ValueError('Message not found')
        return self._serialize_message(message)

    def get_session_messages(self, session_id: uuid.UUID) -> List[Dict]:
        """Get all messages in a session"""
        session = Session.query.get(session_id)
        if not session:
            raise ValueError('Session not found')
        if session.finish_at:
            raise ValueError('Cannot get messages from finished session')

        messages = self.dao.get_session_messages(session_id)
        return [self._serialize_message(msg) for msg in messages]

    def get_conversation_history(self, session_id: uuid.UUID) -> List[Dict[str, str]]:
        """Get conversation history formatted for AI completion"""
        session = Session.query.get(session_id)
        if not session:
            raise ValueError('Session not found')
        if session.finish_at:
            raise ValueError('Cannot get messages from finished session')

        messages = self.dao.get_session_messages(session_id)
        return [
            {"role": msg.role, "content": msg.content}
            for msg in messages
        ]

    def create_message(self, session_id: uuid.UUID, user_id: uuid.UUID,
                      content: str, role: str, vector=None, metadata=None) -> Dict:
        """Create a new message with embedding vector"""
        session = Session.query.get(session_id)
        if not session:
            raise ValueError('Session not found')
        if session.finish_at:
            raise ValueError('Cannot create message in finished session')
            
        message = self.dao.create_message(
            session_id=session_id,
            user_id=user_id,
            content=content,
            role=role,
            vector=vector,
            metadata=metadata
        )

        return self._serialize_message(message)
    def create_langgraph_completion(self, session_id: uuid.UUID, user_id: uuid.UUID, 
                                  content: str = None, messages: List[Union[BaseMessage, Dict[str, Any]]] = None) -> Generator[str, None, None]:
        """LangGraph를 통한 응답 생성.
        
        Args:
            session_id: 세션 ID
            user_id: 사용자 ID
            content: 사용자 메시지 내용 (단일 메시지인 경우)
            messages: 입력 메시지 리스트 (여러 메시지인 경우)
        
        Yields:
            SSE 형식의 메시지 스트림
        """
        logger = logging.getLogger(__name__)
        logger.debug(f"Create LangGraph completion called with: session_id={session_id}, user_id={user_id}")

        try:
            # content가 전달된 경우 HumanMessage로 변환
            if content is not None and messages is None:
                messages = [HumanMessage(content=content)]
                logger.debug(f"Created messages from content: {messages}")

            if not messages:
                raise ValueError("Either content or messages must be provided")

            # 사용자 메시지 저장
            user_message = format_message_content(messages[-1], str(session_id), str(user_id))
            logger.debug(f"Formatted user message: {user_message}")
            
            if user_message["content"] or user_message.get("metadata"):  # 내용이나 메타데이터가 있는 경우 저장
                self.dao.create_message(
                    session_id=session_id,
                    user_id=user_id,
                    content=user_message["content"],
                    role=user_message["role"],
                    metadata=user_message["metadata"]
                )
                yield f"data: {json.dumps(user_message)}\n\n"
            
            # LangGraph 실행
            logger.debug("Starting LangGraph execution")
            initial_state = {"messages": messages}
            
            for chunk in self.graph.stream(initial_state):
                logger.debug(f"Received chunk: {chunk}")
                formatted_msg = None
                
                if isinstance(chunk, (AIMessage, ToolMessage)):
                    formatted_msg = format_message_content(chunk, str(session_id), str(user_id))
                    logger.debug(f"Formatted message from BaseMessage: {formatted_msg}")
                    
                elif isinstance(chunk, dict) and ("content" in chunk or "metadata" in chunk):  # content나 metadata 중 하나라도 있으면 처리
                    role = chunk.get("role", "assistant")
                    # Tool 메시지의 경우 role을 보존
                    if "tool_calls" in chunk.get("metadata", {}) or "tool_name" in chunk.get("metadata", {}):
                        role = "tool"
                        
                    formatted_msg = {
                        "content": chunk.get("content", ""),  # content가 없으면 빈 문자열
                        "role": role,
                        "metadata": chunk.get("metadata"),
                        "session_id": str(session_id),
                        "user_id": str(user_id)
                    }
                    logger.debug(f"Formatted message from dict: {formatted_msg}")

                if formatted_msg and (formatted_msg["content"] or formatted_msg.get("metadata")):  # 내용이나 메타데이터가 있는 경우 처리
                    self.dao.create_message(
                        session_id=session_id,
                        user_id=user_id,
                        content=formatted_msg["content"],
                        role=formatted_msg["role"],
                        metadata=formatted_msg["metadata"]
                    )
                    yield f"data: {json.dumps(formatted_msg)}\n\n"
                    
        except Exception as e:
            logger.error(f"Error in create_langgraph_completion: {e}", exc_info=True)
            error_msg = {
                "content": f"죄송합니다. 응답을 생성하는 동안 오류가 발생했습니다. ({str(e)})",
                "role": "assistant",
                "metadata": {"error": str(e)},
                "session_id": str(session_id),
                "user_id": str(user_id)
            }
            
            self.dao.create_message(
                session_id=session_id,
                user_id=user_id,
                content=error_msg["content"],
                role=error_msg["role"],
                metadata=error_msg["metadata"]
            )
            
            yield f"data: {json.dumps(error_msg)}\n\n"
