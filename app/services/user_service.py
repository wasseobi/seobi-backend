import uuid
from typing import List, Optional, Dict, Any

from langchain_core.messages import BaseMessage

from app.dao.user_dao import UserDAO
from app.utils.agent_state_store import AgentStateStore
from app.utils.openai_client import get_completion
from app.utils.prompt.service_prompts import USER_MEMORY_SYSTEM_PROMPT

class UserService:
    def __init__(self):
        self.user_dao = UserDAO()

    def _serialize_user(self, user: Any) -> Dict[str, Any]:
        """Serialize user data for API response"""
        return {
            'id': str(user.id),
            'username': user.username,
            'email': user.email
        }

    def get_all_users(self) -> List[Dict]:
        users = self.user_dao.get_all()
        return [self._serialize_user(user) for user in users]

    def get_user_by_id(self, user_id: uuid.UUID) -> Optional[Dict]:
        user = self.user_dao.get(str(user_id))
        if not user:
            return None
        return self._serialize_user(user)

    def get_user_by_email(self, email: str) -> Optional[Dict]:
        user = self.user_dao.get_by_email(email)
        if not user:
            return None
        return self._serialize_user(user)

    def get_user_by_username(self, username: str) -> Optional[Dict]:
        user = self.user_dao.get_by_username(username)
        if not user:
            return None
        return self._serialize_user(user)

    def create_user(self, username: str, email: str) -> Dict:
        if self.user_dao.get_by_email(email):
            raise ValueError("User with this email already exists")
        if self.user_dao.get_by_username(username):
            raise ValueError("User with this username already exists")
            
        user = self.user_dao.create(username=username, email=email)
        return self._serialize_user(user)

    def update_user(self, user_id: uuid.UUID, username: Optional[str] = None, email: Optional[str] = None) -> Optional[Dict]:
        if email and self.user_dao.get_by_email(email):
            raise ValueError("Email already in use")
        if username and self.user_dao.get_by_username(username):
            raise ValueError("Username already in use")
            
        user = self.user_dao.update(user_id=user_id, username=username, email=email)
        if not user:
            return None
        return self._serialize_user(user)

    def delete_user(self, user_id: uuid.UUID) -> bool:
        return self.user_dao.delete(str(user_id))

    def update_user_memory_with_llm(self, user_id: str, summary: Optional[str], messages: List[BaseMessage]) -> Optional[str]:
        """
        summary와 messages, 기존 user_memory를 LLM에 입력해 장기기억(user_memory)을 통합/업데이트
        """
        prev_memory = self.user_dao.get_memory(user_id) or ""

        user_prompt = (
        f"[기존 장기기억]\n{prev_memory}\n\n"
        f"[최근 대화 요약]\n{summary or ''}\n\n"
        f"[최근 메시지]\n{messages}"
        )

        llm_messages = [
            {"role": "system", "content": USER_MEMORY_SYSTEM_PROMPT},
            {"role": "user", "content": user_prompt}
        ]
        updated_memory = get_completion(llm_messages)
        return self.user_dao.update_user_memory(user_id, user_memory=updated_memory)

    def initialize_agent_state(self, user_id: str) -> dict:
        """대화 세션 시작 시 AgentState에 user_memory를 반영"""
        user_memory = self.user_dao.get_memory(user_id)

        previous_state = AgentStateStore.get(user_id) or {}
        previous_messages = previous_state.get('messages', [])
        previous_summary = previous_state.get('summary')

        return {
            # 이전 상태에서 유지할 항목들
            "messages": previous_messages,
            "summary": previous_summary,
            "user_memory": user_memory,

            # 사용자 관련 정보
            "user_id": user_id,
            "user_location": None,

            # 매 대화마다 초기화되어야 하는 항목들
            "current_input": "",
            "scratchpad": [],
            "next_step": None,
            "step_count": 0,
            "tool_results": None,
            "current_tool_call_id": None,
            "current_tool_name": None,
            "current_tool_calls": None
        }

    def save_user_memory_from_state(self, user_id: str, agent_state: dict) -> Optional[str]:
        """대화 세션 종료 시 AgentState의 summary/messages를 활용해 user_memory를 LLM으로 업데이트"""
        summary = agent_state.get("summary")
        messages = agent_state.get("messages", [])
        return self.update_user_memory_with_llm(user_id, summary, messages)