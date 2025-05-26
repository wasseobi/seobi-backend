from app.dao.message_dao import MessageDAO
from app.services.session_service import SessionService
from app.models import Session
from app.utils.message.message_context import MessageContext  # 새로 추가

from app.utils.openai_client import get_openai_client, get_embedding
from app.utils.message.processor import MessageProcessor
from app.utils.message.formatter import format_message_content
from app.langgraph.executor import create_agent_executor
from app.langgraph.graph import build_graph

from langchain.schema import HumanMessage, AIMessage
from langchain_core.messages import BaseMessage, ToolMessage
from typing import List, Dict, Any, Generator, Union, Optional
import uuid
from datetime import datetime, timezone
import logging
import json

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)


class MessageService:
    def __init__(self):
        self.dao = MessageDAO()
        self.session_service = SessionService()
        self.agent_executor = create_agent_executor()
        self.graph = build_graph().compile()
        self.active_contexts: Dict[str, MessageContext] = {}  # 세션별 활성 컨텍스트

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
                       content: str, role: str, metadata) -> Dict:
        """Create a new message (임베딩 벡터 포함)"""
        session = Session.query.get(session_id)
        if not session:
            raise ValueError('Session not found')
        if session.finish_at:
            raise ValueError('Cannot add message to finished session')

        # TODO: 임베딩 벡터 문제 있는 것 같아서 잠깐 주석했어요
        # client = get_openai_client()
        # vector = get_embedding(client, content)
        vector = None

        message = self.dao.create_message(
            session_id, user_id, content, role, vector, metadata)
        return self._serialize_message(message)

    def update_message(self, message_id: uuid.UUID, **kwargs) -> Dict:
        """Update a message"""
        message = self.dao.update_message(message_id, **kwargs)
        if not message:
            raise ValueError('Message not found')
        return self._serialize_message(message)

    def delete_message(self, message_id: uuid.UUID) -> bool:
        """Delete a message"""
        return self.dao.delete_message(message_id)

    def create_langgraph_completion(self, session_id: uuid.UUID, user_id: uuid.UUID,
                                    content: str = None, messages: List[Union[BaseMessage, Dict[str, Any]]] = None) -> Generator[Dict, None, None]:
        """LangGraph를 통한 응답 생성."""
        processor = MessageProcessor(str(session_id), str(user_id))
        context = self._get_or_create_context(str(session_id), str(user_id))
        
        try:
            # 사용자 메시지는 컨텍스트에만 추가 (DB 저장은 나중에)
            context.add_user_message(content if content is not None else messages[-1]['content'])
            
            # 시작 메시지 전송
            yield {
                'type': 'start',
                'user_message': {'content': content}
            }

            # 초기 상태 설정
            messages = [HumanMessage(
                content=content if content is not None else messages[-1]['content'])]
            initial_state = {"messages": messages}

            # LangGraph 메시지 스트리밍 처리
            for msg_chunk, metadata in self.graph.stream(initial_state, stream_mode="messages"):
                try:
                    # 도구 호출 메시지 처리
                    if isinstance(msg_chunk, ToolMessage):
                        # 도구 응답 처리 및 전송
                        for processed in processor.process_ai_or_tool_message(msg_chunk):
                            context.add_tool_result(
                                tool_name=processed.get("metadata", {}).get("tool_name", "unknown"),
                                result=processed.get("content", "")
                            )
                            yield {
                                'type': 'chunk',
                                'content': processed.get("content", ""),
                                'metadata': {
                                    **processed.get("metadata", {}),
                                    "tool_response": True
                                }
                            }

                    # AI 메시지 처리
                    elif isinstance(msg_chunk, AIMessage):
                        # 도구 호출이 있는 경우
                        if hasattr(msg_chunk, "additional_kwargs") and msg_chunk.additional_kwargs.get("tool_calls"):
                            tool_calls = msg_chunk.additional_kwargs["tool_calls"]
                            context.add_tool_call_chunk(tool_calls[0])  # 현재는 하나의 도구 호출만 처리
                            yield {
                                'type': 'tool_calls',
                                'tool_calls': tool_calls
                            }
                        # 일반 응답 내용이 있는 경우
                        elif msg_chunk.content:
                            context.append_assistant_content(msg_chunk.content)
                            yield {
                                'type': 'chunk',
                                'content': msg_chunk.content,
                                'metadata': metadata
                            }

                    # 기타 메시지 처리
                    elif isinstance(msg_chunk, dict):
                        if "agent" in msg_chunk:
                            messages_to_process = msg_chunk["agent"].get("formatted_messages", [])
                            for processed in processor.process_agent_messages(messages_to_process):
                                if processed.get("content"):
                                    context.append_assistant_content(processed["content"])
                                    yield {
                                        'type': 'chunk',
                                        'content': processed["content"],
                                        'metadata': processed.get("metadata", {})
                                    }
                        elif "content" in msg_chunk or "metadata" in msg_chunk:
                            for processed in processor.process_dict_message(msg_chunk):
                                if processed.get("content"):
                                    context.append_assistant_content(processed["content"])
                                    yield {
                                        'type': 'chunk',
                                        'content': processed["content"],
                                        'metadata': processed.get("metadata", metadata)
                                    }

                except Exception as processing_error:
                    logger.error(f"메시지 처리 중 오류 발생: {str(processing_error)}")
                    continue

            # 대화 완료 처리
            context.finalize_assistant_response()
            self._save_context_messages(context)  # 모든 메시지를 한 번에 저장

            # 완료 메시지 전송
            yield {
                'type': 'end',
                'context_saved': True
            }

        except Exception as e:
            logger.error(f"LangGraph 완료 생성 중 오류 발생: {str(e)}")
            yield {
                'type': 'error',
                'error': str(e)
            }
            raise

    def get_user_messages(self, user_id: uuid.UUID) -> List[Dict]:
        """Get all messages for a user

        Args:
            user_id (uuid.UUID): User's ID

        Returns:
            List[Dict]: List of serialized messages for the user

        Raises:
            ValueError: If user_id is invalid
        """
        try:
            messages = self.dao.get_user_messages(user_id)
            return [self._serialize_message(msg) for msg in messages]
        except Exception as e:
            raise ValueError(f"Failed to get messages for user {user_id}")

    def _get_or_create_context(self, session_id: str, user_id: str) -> MessageContext:
        """세션에 대한 메시지 컨텍스트를 가져오거나 생성합니다."""
        context_key = str(session_id)
        if context_key not in self.active_contexts:
            self.active_contexts[context_key] = MessageContext(
                session_id=str(session_id),
                user_id=str(user_id)
            )
        return self.active_contexts[context_key]

    def _save_context_messages(self, context: MessageContext) -> None:
        """컨텍스트의 모든 메시지를 DB에 저장합니다."""
        try:
            session_id = uuid.UUID(context.session_id)
            user_id = uuid.UUID(context.user_id)

            logger.debug(f"메시지 저장 시작 - 세션: {session_id}")
            messages = context.get_messages_for_storage()
            logger.debug(f"저장할 메시지: {json.dumps(messages, ensure_ascii=False)}")

            for message in messages:
                try:
                    # timestamp는 메타데이터에서 DB 필드로 이동
                    if "timestamp" in message:
                        timestamp = message.pop("timestamp")
                    else:
                        timestamp = datetime.now(timezone.utc).isoformat()

                    metadata = message.get("metadata", {})
                    if isinstance(metadata, dict) and "timestamp" in metadata:
                        del metadata["timestamp"]

                    logger.debug(f"메시지 저장 시도: role={message['role']}, metadata={json.dumps(metadata, ensure_ascii=False)}")

                    self.create_message(
                        session_id=session_id,
                        user_id=user_id,
                        content=message["content"],
                        role=message["role"],
                        metadata=metadata
                    )
                    logger.debug(f"메시지 저장 성공: {message['role']}")
                except Exception as msg_error:
                    logger.error(f"개별 메시지 저장 실패: {str(msg_error)}")
                    raise

            # 컨텍스트 제거
            self.active_contexts.pop(context.session_id, None)
            logger.debug(f"모든 메시지 저장 완료 - 세션: {session_id}")

        except Exception as e:
            logger.error(f"메시지 저장 중 오류 발생: {str(e)}")
            raise
