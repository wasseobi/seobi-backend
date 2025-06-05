import uuid
from typing import Optional

from app.dao.base import BaseDAO
from app.models.user import User

class UserDAO(BaseDAO[User]):
    """Data Access Object for User model"""
    
    def __init__(self):
        super().__init__(User)

    def get_by_email(self, email: str) -> Optional[User]:
        return self.query().filter_by(email=email).first()

    def get_by_username(self, username: str) -> Optional[User]:
        return self.query().filter_by(username=username).first()

    def get_memory(self, user_id: uuid.UUID) -> Optional[dict]:
        user = self.get(str(user_id))
        if user:
            return user.user_memory
        return None
    
    def update_user_memory(self, user_id: uuid.UUID, user_memory: dict) -> Optional[User]:
        return super().update(str(user_id), user_memory=user_memory) 
    
    def create(self, username: str, email: str) -> User:
        return super().create(username=username, email=email)

    def update(self, user_id: uuid.UUID, username: Optional[str] = None, email: Optional[str] = None) -> Optional[User]:
        return super().update(str(user_id), username=username, email=email) 
    