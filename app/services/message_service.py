from app.dao.message_dao import MessageDAO
from app.services.session_service import SessionService
from app.models import Session
from app.models.db import db
from app.utils.openai_client import get_openai_client, get_completion, get_embedding
from app.langgraph.graph import build_graph as langgraph_builder
from app.langgraph.executor import create_agent_executor
from langchain.schema import HumanMessage, AIMessage
from typing import List, Dict, Any, AsyncGenerator
from datetime import datetime
import uuid
import json


class MessageService:
    def __init__(self):
        self.dao = MessageDAO()
        self.session_service = SessionService()
        self.agent = create_agent_executor()
        self.graph = langgraph_builder()

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
                      content: str, role: str = 'user', vector=None, metadata=None) -> Dict:
        """Create a new message with embedding vector"""
        session = Session.query.get(session_id)
        if not session:
            raise ValueError('Session not found')
        if session.finish_at:
            raise ValueError('Cannot create message in finished session')

        # 임베딩 벡터 생성
        if vector is None and role == 'user':
            embedding = get_embedding(content)
            vector = embedding if embedding is not None else None

        message = self.dao.create_message(
            session_id=session_id,
            user_id=user_id,
            content=content,
            role=role,
            vector=vector,
            metadata=metadata
        )

        return self._serialize_message(message)

    async def create_completion_message(self, session_id: uuid.UUID, user_id: uuid.UUID,
                                     messages: List[Dict]) -> AsyncGenerator[Dict, None]:
        """Create an AI completion message"""
        session = Session.query.get(session_id)
        if not session:
            raise ValueError('Session not found')
        if session.finish_at:
            raise ValueError('Cannot create message in finished session')

        # 스트림 응답을 담을 변수
        full_response = ""
        metadata = {}

        try:
            # AI 응답 생성 시작
            async for chunk in await self.graph.arun(messages):
                if isinstance(chunk, dict) and 'type' in chunk:
                    if chunk['type'] == 'metadata':
                        metadata.update(chunk['content'])
                    continue
                message_content = chunk.content if isinstance(chunk, AIMessage) else str(chunk)
                full_response += message_content
                yield {'content': message_content, 'type': 'chunk'}

            # 최종 메시지 저장
            message = self.dao.create_message(
                session_id=session_id,
                user_id=user_id,
                content=full_response,
                role='assistant',
                metadata=metadata
            )
            
            serialized_message = self._serialize_message(message)
            yield {'content': serialized_message, 'type': 'message'}
            
        except Exception as e:
            raise ValueError(f"Failed to create completion message: {str(e)}")
