from app.dao.base import BaseDAO
from app.models.user import User
from typing import Optional
import uuid

class UserDAO(BaseDAO[User]):
    """Data Access Object for User model"""
    
    def __init__(self):
        super().__init__(User)

    def get_by_email(self, email: str) -> Optional[User]:
        """Get a user by email"""
        return self.query().filter_by(email=email).first()

    def get_by_username(self, username: str) -> Optional[User]:
        """Get a user by username"""
        return self.query().filter_by(username=username).first()

    def create_user(self, username: str, email: str) -> User:
        """Create a new user with specific fields"""
        return self.create(username=username, email=email)

    def update_user(self, user_id: uuid.UUID, username: Optional[str] = None, email: Optional[str] = None) -> Optional[User]:
        """Update a user with specific fields"""
        return self.update(str(user_id), username=username, email=email) 