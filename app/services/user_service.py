import uuid
from typing import List, Optional, Dict, Any

from app.dao.user_dao import UserDAO

class UserService:
    def __init__(self):
        self.user_dao = UserDAO()

    def _serialize_user(self, user: Any) -> Dict[str, Any]:
        """Serialize user data for API response"""
        return {
            'id': str(user.id),
            'username': user.username,
            'email': user.email,
            'user_memory': user.user_memory
        }

    # NOTE(GideokKim): 유저가 없을 경우엔 빈 리스트를 반환하는 것은 정상적인 동작이므로 예외처리 필요 없음.
    def get_all_users(self) -> List[Dict]:
        users = self.user_dao.get_all()
        return [self._serialize_user(user) for user in users]

    def get_user_by_id(self, user_id: uuid.UUID) -> Dict:
        user = self.user_dao.get(str(user_id))
        if not user:
            raise ValueError(f'User with id {user_id} not found')
        return self._serialize_user(user)

    def get_user_by_email(self, email: str) -> Dict:
        user = self.user_dao.get_by_email(email)
        if not user:
            raise ValueError(f'User with email {email} not found')
        return self._serialize_user(user)

    def get_user_by_username(self, username: str) -> Dict:
        user = self.user_dao.get_by_username(username)
        if not user:
            raise ValueError(f'User with username {username} not found')
        return self._serialize_user(user)

    # NOTE(GideokKim): 현재 user table model 구조상 이메일과 유저네임은 유니크해야 하므로 중복 체크 필요.
    # TODO(GideokKim): 나중에 유저네임이 유니크하지 않아도 되도록(동명이인이 있을 수 있도록) 수정해야 함.
    def create_user(self, username: str, email: str) -> Dict:
        if self.user_dao.get_by_email(email):
            raise ValueError("User with this email already exists")
        if self.user_dao.get_by_username(username):
            raise ValueError("User with this username already exists")
            
        user = self.user_dao.create(username=username, email=email)
        return self._serialize_user(user)

    # NOTE(GideokKim): 현재 user table model 구조상 이메일과 유저네임은 유니크해야 하므로 중복 체크 필요.
    # TODO(GideokKim): 나중에 유저네임이 유니크하지 않아도 되도록(동명이인이 있을 수 있도록) 수정해야 함.
    def update_user(self, user_id: uuid.UUID, username: Optional[str] = None, email: Optional[str] = None) -> Dict:
        if email and self.user_dao.get_by_email(email):
            raise ValueError("Email already in use")
        if username and self.user_dao.get_by_username(username):
            raise ValueError("Username already in use")
            
        user = self.user_dao.update(user_id=user_id, username=username, email=email)
        if not user:
            raise ValueError(f'User with id {user_id} not found')
        return self._serialize_user(user)

    def delete_user(self, user_id: uuid.UUID) -> bool:
        return self.user_dao.delete(str(user_id))

    # TODO(GideokKim): Test 코드 작성 필요
    def get_user_memory(self, user_id: uuid.UUID) -> str:
        """사용자의 장기 기억(메모리) 조회"""
        user = self.user_dao.get(str(user_id))
        if not user:
            raise ValueError(f'User with id {user_id} not found')
        return user.user_memory

    # TODO(GideokKim): Test 코드 작성 필요
    def update_user_memory(self, user_id: uuid.UUID, memory_data: str) -> str:
        """사용자의 장기 기억(메모리) 저장/업데이트"""
        user = self.user_dao.update_user_memory(user_id, user_memory=memory_data)
        if not user:
            raise ValueError(f'User with id {user_id} not found')
        return self._serialize_user(user)