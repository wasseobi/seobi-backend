from app.dao.base import BaseDAO
from app.models import Message
from typing import List, Optional
import uuid

class MessageDAO(BaseDAO[Message]):
    """Data Access Object for Message model"""
    
    def __init__(self):
        super().__init__(Message)

    def get_all_messages(self) -> List[Message]:
        """Get all messages ordered by timestamp"""
        return self.query().order_by(Message.timestamp.asc()).all()

    def get_message_by_id(self, message_id: uuid.UUID) -> Optional[Message]:
        """Get a message by ID"""
        return self.get(str(message_id))

    def get_session_messages(self, session_id: uuid.UUID) -> List[Message]:
        """Get all messages in a session ordered by timestamp"""
        return self.query().filter_by(session_id=session_id).order_by(Message.timestamp.asc()).all()

    def create_message(self, session_id: uuid.UUID, user_id: uuid.UUID, 
                      content: str, role: str = 'user') -> Message:
        """Create a new message"""
        return self.create(
            session_id=session_id,
            user_id=user_id,
            content=content,
            role=role
        )

    def update_message(self, message_id: uuid.UUID, **kwargs) -> Optional[Message]:
        """Update a message"""
        return self.update(str(message_id), **kwargs)

    def delete_message(self, message_id: uuid.UUID) -> bool:
        """Delete a message"""
        return self.delete(str(message_id))

    def get_user_messages(self, user_id: uuid.UUID) -> List[Message]:
        """Get all messages for a user ordered by timestamp

        Args:
            user_id (uuid.UUID): User's ID

        Returns:
            List[Message]: List of messages for the user
        """
        return self.query().filter_by(user_id=user_id).order_by(Message.timestamp.desc()).all()