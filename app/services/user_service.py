from app.dao.user_dao import UserDAO
from typing import List, Optional, Dict, Any
import uuid

class UserService:
    def __init__(self):
        self.dao = UserDAO()

    def _serialize_user(self, user: Any) -> Dict[str, Any]:
        """Serialize user data for API response"""
        return {
            'id': str(user.id),
            'username': user.username,
            'email': user.email
        }

    def get_all_users(self) -> List[Dict]:
        """Get all users"""
        users = self.dao.get_all()
        return [self._serialize_user(user) for user in users]

    def get_user_by_id(self, user_id: uuid.UUID) -> Optional[Dict]:
        """Get a user by ID"""
        user = self.dao.get(str(user_id))
        if not user:
            return None
        return self._serialize_user(user)

    def get_user_by_email(self, email: str) -> Optional[Dict]:
        """Get a user by email"""
        user = self.dao.get_by_email(email)
        if not user:
            return None
        return self._serialize_user(user)

    def get_user_by_username(self, username: str) -> Optional[Dict]:
        """Get a user by username"""
        user = self.dao.get_by_username(username)
        if not user:
            return None
        return self._serialize_user(user)

    def create_user(self, username: str, email: str) -> Dict:
        """Create a new user with validation"""
        if self.dao.get_by_email(email):
            raise ValueError("User with this email already exists")
        if self.dao.get_by_username(username):
            raise ValueError("User with this username already exists")
            
        user = self.dao.create(username=username, email=email)
        return self._serialize_user(user)

    def update_user(self, user_id: uuid.UUID, username: Optional[str] = None, email: Optional[str] = None) -> Optional[Dict]:
        """Update a user with validation"""
        if email and self.dao.get_by_email(email):
            raise ValueError("Email already in use")
        if username and self.dao.get_by_username(username):
            raise ValueError("Username already in use")
            
        user = self.dao.update(user_id=user_id, username=username, email=email)
        if not user:
            return None
        return self._serialize_user(user)

    def delete_user(self, user_id: uuid.UUID) -> bool:
        """Delete a user"""
        return self.dao.delete(str(user_id)) 