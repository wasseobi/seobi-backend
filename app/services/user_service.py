from app.dao.user_dao import UserDAO
from typing import List, Optional, Dict, Any
import uuid
from app.utils.openai_client import get_openai_client, get_completion
from langchain_core.messages import BaseMessage

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

    def get_user_memory(self, user_id: uuid.UUID) -> Optional[str]:
        """사용자의 장기 기억(메모리) 조회"""
        return self.dao.get_user_memory(user_id)

    def update_user_memory(self, user_id: uuid.UUID, memory_data: str) -> Optional[str]:
        """사용자의 장기 기억(메모리) 저장/업데이트"""
        return self.dao.update_user_memory(user_id, memory_data)

    def update_user_memory_with_llm(self, user_id: str, summary: Optional[str], messages: List[BaseMessage]) -> Optional[str]:
        """
        summary와 messages, 기존 user_memory를 LLM에 입력해 장기기억(user_memory)을 통합/업데이트
        """
        prev_memory = self.get_user_memory(user_id) or ""
        # 최근 메시지 3개만 추출
        important_msgs = [m.content for m in messages if hasattr(m, "content") and m.content]
        recent_msgs = "\n".join(important_msgs[-3:]) if important_msgs else ""
        prompt = (
        "당신은 사용자의 장기기억을 생성 및 관리하는 AI입니다.\n\n"
        "아래는 세 가지 정보입니다:\n"
        "- [기존 장기기억]: 현재까지 저장된 사용자 정보\n"
        "- [최근 대화 요약]: 최근 대화의 핵심 내용 요약\n"
        "- [최근 메시지]: 사용자의 가장 최근 발화 내용\n\n"
        "이 세 정보를 종합해 **사용자의 장기기억을 업데이트** 해주세요.\n\n"
        "작성 기준은 다음과 같습니다:\n"
        "1. 중복된 정보는 제거하고, 더 구체적인 내용으로 갱신하세요.\n"
        "2. 불필요하거나 일시적인 내용은 포함하지 마세요 (예: 감탄사, 잡담, 일회성 요청 등).\n"
        "3. 정보 간 맥락을 고려하여 정리하고, 핵심 사실만 명확하게 정제하세요.\n"
        "4. 기존 장기기억의 구조를 유지하면서 필요한 부분만 보완하거나 교체하세요.\n"
        "5. 출력은 평문 텍스트로, 항목별 줄바꿈을 유지하세요.\n\n"
        f"[기존 장기기억]\n{prev_memory}\n\n"
        f"[최근 대화 요약]\n{summary or ''}\n\n"
        f"[최근 메시지]\n{recent_msgs}\n\n"
        )
        client = get_openai_client()
        llm_messages = [
            {"role": "system", "content": "아래 정보를 바탕으로 사용자의 장기기억을 최신화해줘."},
            {"role": "user", "content": prompt}
        ]
        updated_memory = get_completion(client, llm_messages)
        return self.update_user_memory(user_id, updated_memory)

    def initialize_agent_state(self, user_id: str) -> dict:
        """대화 세션 시작 시 AgentState에 user_memory를 반영"""
        user_memory = self.get_user_memory(user_id)
        return {
            "messages": [],
            "summary": None,
            "user_memory": user_memory,
            "user_id": user_id,
            "current_input": "",
            "scratchpad": [],
            "next_step": None
        }

    def save_user_memory_from_state(self, user_id: str, agent_state: dict) -> Optional[str]:
        """대화 세션 종료 시 AgentState의 summary/messages를 활용해 user_memory를 LLM으로 업데이트"""
        summary = agent_state.get("summary")
        messages = agent_state.get("messages", [])
        return self.update_user_memory_with_llm(user_id, summary, messages)