from app.dao.message_dao import MessageDAO
from app.services.session_service import SessionService
from app.models import Session
from app.models.db import db
from app.utils.openai_client import get_openai_client, get_completion
from app.langgraph.graph import builder as langgraph_builder
from langchain.schema import HumanMessage
from typing import List, Dict, Any
from datetime import datetime
import uuid


class MessageService:
    def __init__(self):
        self.dao = MessageDAO()
        self.session_service = SessionService()

    def _serialize_message(self, message: Any) -> Dict[str, Any]:
        """Serialize message data for API response"""
        return {
            'id': str(message.id),
            'session_id': str(message.session_id),
            'user_id': str(message.user_id),
            'content': message.content,
            'role': message.role,
            'timestamp': message.timestamp.isoformat() if message.timestamp else None,
            'vector': message.vector.tolist() if message.vector is not None else None
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
                       content: str, role: str = 'user') -> Dict:
        """Create a new message"""
        session = Session.query.get(session_id)
        if not session:
            raise ValueError('Session not found')
        if session.finish_at:
            raise ValueError('Cannot add message to finished session')

        message = self.dao.create_message(session_id, user_id, content, role)
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

    def create_completion(self, session_id: uuid.UUID, user_id: uuid.UUID,
                          content: str) -> Dict[str, Dict]:
        """Create a new message and get AI completion"""
        session = Session.query.get(session_id)
        if not session:
            raise ValueError('Session not found')
        if session.finish_at:
            raise ValueError('Cannot add message to finished session')

        # Create user message
        user_message = self.dao.create_message(
            session_id, user_id, content, 'user')

        # Get conversation history
        history = self.get_conversation_history(session_id)

        # Prepare messages for OpenAI
        messages = [
            {"role": "system", "content": "당신은 도움이 되는 AI 어시스턴트입니다. 응답은 간결하고 명확하게 해주세요."},
            *history,
            {"role": "user", "content": content}
        ]

        # Get AI completion
        try:
            client = get_openai_client()
            response = get_completion(client, messages)
        except Exception as e:
            raise ValueError(f"Failed to get AI completion: {str(e)}")

        # Create assistant message
        assistant_message = self.dao.create_message(
            session_id, user_id, response, 'assistant')

        # Update session title and description if this is the first message
        if len(history) == 1:
            self.session_service.update_title_description_from_conversation(
                session_id, content, response
            )

        return {
            'user_message': self._serialize_message(user_message),
            'assistant_message': self._serialize_message(assistant_message)
        }

    def create_langgraph_completion(self, session_id: uuid.UUID, user_id: uuid.UUID, content: str) -> Dict[str, Dict]:
        """LangGraph 기반으로 메시지 생성 및 AI 응답/저장"""
        try:

            # DB 트랜잭션 시작
            db.session.begin(nested=True)

            # 1. 사용자 메시지 저장
            user_message = self.create_message(
                session_id, user_id, content, 'user')

            # 2. 랭그래프 상태 생성 및 실행
            initial_state = {
                "user_input": content,
                "parsed_intent": {},
                "reply": "",
                "action_required": False,
                "executed_result": {},
                "timestamp": datetime.utcnow().isoformat(),
                "user_id": str(user_id),
                "session_id": str(session_id),
                "tool_info": None,
                "messages": [HumanMessage(content=content)]
            }

            graph = langgraph_builder.compile()
            result = graph.invoke(initial_state)
            ai_reply = result.get("reply", "")

            # 3. AI 메시지 저장
            assistant_message = self.create_message(
                session_id=session_id,
                user_id=user_id,
                content=ai_reply,
                role='assistant'
            )

            # 트랜잭션 커밋
            db.session.commit()

            return {
                'user_message': user_message,
                'assistant_message': assistant_message
            }

        except Exception as e:
            # 오류 발생 시 롤백
            db.session.rollback()
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
