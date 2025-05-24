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
        """LangGraph를 통한 응답 생성."""
        session_info = {
            "session_id": str(session_id),
            "user_id": str(user_id)
        }
        
        try:
            if content is not None and messages is None:
                messages = [HumanMessage(content=content)]

            if not messages:
                raise ValueError("Either content or messages must be provided")
            
            initial_state = {"messages": messages}
            seen_messages = set()
            
            for chunk in self.graph.stream(initial_state):
                try:
                    if isinstance(chunk, dict) and chunk.get("agent"):
                        messages_to_process = chunk["agent"].get("formatted_messages", [])
                        
                        for msg in messages_to_process:
                            if not isinstance(msg, dict):
                                continue
                                
                            msg_content = msg.get("content", "").strip()
                            msg_metadata = msg.get("metadata", {}) or {}
                            
                            if not (msg_content or msg_metadata):
                                continue
                                
                            role = msg.get("role", "assistant")
                            if msg_metadata.get("type") == "tool_response" or \
                               (msg_metadata.get("tool_name") and not "tool_calls" in msg_metadata) or \
                               msg_metadata.get("original_role") == "tool":
                                role = "tool"
                            elif "tool_calls" in msg_metadata:
                                role = "assistant"
                                
                            formatted_msg = {
                                "content": msg_content,
                                "role": role,
                                "metadata": msg_metadata if msg_metadata and any(msg_metadata.values()) else None,
                                **session_info
                            }
                            
                            msg_key = self._get_message_key(formatted_msg)
                            if msg_key in seen_messages:
                                continue
                                
                            seen_messages.add(msg_key)
                            
                            saved_message = self.dao.create_message(
                                session_id=session_id,
                                user_id=user_id,
                                content=formatted_msg["content"],
                                role=formatted_msg["role"],
                                metadata=formatted_msg["metadata"]
                            )
                            yield f"data: {json.dumps(formatted_msg, ensure_ascii=False)}\n\n"
                    
                    elif isinstance(chunk, (AIMessage, ToolMessage)):
                        formatted_msg = format_message_content(chunk, **session_info)
                        msg_key = self._get_message_key(formatted_msg)
                        
                        if msg_key not in seen_messages:
                            seen_messages.add(msg_key)
                            saved_message = self.dao.create_message(
                                session_id=session_id,
                                user_id=user_id,
                                content=formatted_msg["content"],
                                role=formatted_msg["role"],
                                metadata=formatted_msg["metadata"]
                            )
                            yield f"data: {json.dumps(formatted_msg, ensure_ascii=False)}\n\n"
                            
                    elif isinstance(chunk, dict) and ("content" in chunk or "metadata" in chunk):
                        content = chunk.get("content", "").strip()
                        metadata = chunk.get("metadata", {}) or {}
                        role = chunk.get("role", "assistant")
                        
                        if metadata.get("type") == "tool_response" or \
                           (metadata.get("tool_name") and not "tool_calls" in metadata) or \
                           metadata.get("original_role") == "tool":
                            role = "tool"
                        elif "tool_calls" in metadata:
                            role = "assistant"
                            
                        formatted_msg = {
                            "content": content,
                            "role": role,
                            "metadata": metadata if metadata and any(metadata.values()) else None,
                            **session_info
                        }
                        
                        msg_key = self._get_message_key(formatted_msg)
                        if msg_key not in seen_messages:
                            seen_messages.add(msg_key)
                            saved_message = self.dao.create_message(
                                session_id=session_id,
                                user_id=user_id,
                                content=formatted_msg["content"],
                                role=formatted_msg["role"],
                                metadata=formatted_msg["metadata"]
                            )
                            yield f"data: {json.dumps(formatted_msg, ensure_ascii=False)}\n\n"
                        
                except Exception as e:
                    continue
                
        except Exception as e:
            error_msg = {
                "content": f"죄송합니다. 응답을 생성하는 동안 오류가 발생했습니다. ({str(e)})",
                "role": "assistant",
                "metadata": {"error": str(e)},
                **session_info
            }
            
            saved_message = self.dao.create_message(
                session_id=session_id,
                user_id=user_id,
                content=error_msg["content"],
                role=error_msg["role"],
                metadata=error_msg["metadata"]
            )
            yield f"data: {json.dumps(error_msg, ensure_ascii=False)}\n\n"

    def _get_message_key(self, msg: Dict[str, Any]) -> str:
        """메시지의 고유 키를 생성하는 함수"""
        metadata = msg.get("metadata", {})
        if metadata and msg.get("role") == "tool":
            tool_call_id = metadata.get("tool_call_id")
            if tool_call_id:
                return f"tool_{tool_call_id}"
                
        content = msg.get("content", "").strip()
        role = msg.get("role", "")
        if content and role:
            return f"{role}_{hash(content)}"
            
        if metadata:
            return f"{role}_{hash(str(metadata))}"
            
        return f"{role}_{hash(content)}_{hash(str(metadata))}"
