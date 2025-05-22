import uuid
from app.dao.message_dao import MessageDAO
from app.services.session_service import SessionService
from app.models import Session
from app.utils.openai_client import get_openai_client, get_completion
from typing import List, Dict, Any
from app import db

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
            'vector': message.vector.tolist() if hasattr(message.vector, 'tolist') else (list(message.vector) if message.vector is not None else None)
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
                      content: str, role: str = 'user', vector=None) -> Dict:
        """Create a new message (vector는 None이어도 무방)"""
        session = Session.query.get(session_id)
        if not session:
            raise ValueError('Session not found')
        if session.finish_at:
            raise ValueError('Cannot add message to finished session')

        message = self.dao.create_message(session_id, user_id, content, role, vector)
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
        user_message = self.dao.create_message(session_id, user_id, content, 'user')

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
        assistant_message = self.dao.create_message(session_id, user_id, response, 'assistant')

        # Update session title and description if this is the first message
        if len(history) == 1:
            self.session_service.update_title_description_from_conversation(
                session_id, content, response
            )

        return {
            'user_message': self._serialize_message(user_message),
            'assistant_message': self._serialize_message(assistant_message)
        }

    def vector_search(self, session_id, query_vector, top_k=5):
        # pgvector는 {1,2,3,...} 형식의 문자열로 변환 필요
        vector_str = "{" + ",".join(str(x) for x in query_vector) + "}"
        sql = """
            SELECT *, vector <=> :query_vector AS distance
            FROM message
            WHERE session_id = :session_id
            ORDER BY vector <=> :query_vector
            LIMIT :top_k
        """
        result = db.session.execute(
            db.text(sql),
            {
                'query_vector': vector_str,
                'session_id': str(session_id),
                'top_k': top_k
            }
        )
        # 벡터 필드가 numpy array 등일 경우 float 리스트로 변환
        rows = []
        for row in result:
            row_dict = dict(row)
            if 'vector' in row_dict and hasattr(row_dict['vector'], 'tolist'):
                row_dict['vector'] = row_dict['vector'].tolist()
            elif 'vector' in row_dict and row_dict['vector'] is not None:
                row_dict['vector'] = list(row_dict['vector'])
            rows.append(row_dict)
        return rows 