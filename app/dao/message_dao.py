import uuid
from typing import List, Optional

from app.models import Message
from app.dao.base import BaseDAO

class MessageDAO(BaseDAO[Message]):
    """Data Access Object for Message model"""
    
    def __init__(self):
        super().__init__(Message)

    def get_all_messages(self) -> List[Message]:
        """Get all messages ordered by timestamp"""
        return self.query().order_by(Message.timestamp.asc()).all()

    def get_message_by_id(self, message_id: uuid.UUID) -> Optional[Message]:
        return self.get(str(message_id))

    def get_user_messages(self, user_id: uuid.UUID) -> List[Message]:
        """Get all messages for a user ordered by timestamp"""
        return self.query().filter_by(user_id=user_id).order_by(Message.timestamp.desc()).all()

    def get_session_messages(self, session_id: uuid.UUID) -> List[Message]:
        """Get all messages in a session ordered by timestamp"""
        return self.query().filter_by(session_id=session_id).order_by(Message.timestamp.asc()).all()

    def create(self, session_id: uuid.UUID, user_id: uuid.UUID, 
                      content: str, role: str, vector=None, metadata=None) -> Message:
        """Create a new message (vector 임베딩 포함)"""
        return super().create(
            session_id=session_id,
            user_id=user_id,
            content=content,
            role=role,
            vector=vector,
            message_metadata=metadata
        )

    def update(self, message_id: uuid.UUID, **kwargs) -> Optional[Message]:
        return super().update(str(message_id), **kwargs)
