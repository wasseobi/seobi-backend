from typing import List, Optional
from langchain_core.messages import BaseMessage

from app.services.user_service import UserService
from app.utils.openai_client import get_completion
from app.utils.prompt.service_prompts import USER_MEMORY_SYSTEM_PROMPT

class UserMemoryLLMService:
    def __init__(self):
        self.user_service = UserService()

    def update_user_memory_with_llm(self, user_id: str, summary: Optional[str], messages: List[BaseMessage]) -> Optional[str]:
        """
        summary와 messages, 기존 user_memory를 LLM에 입력해 장기기억(user_memory)을 통합/업데이트
        """
        prev_memory = self.user_service.get_user_memory(user_id) or ""

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
        return self.user_service.update_user_memory(user_id, memory_data=updated_memory)

    def initialize_agent_state(self, user_id: str) -> dict:
        """대화 세션 시작 시 AgentState에 user_memory를 반영"""
        user_memory = self.user_service.get_user_memory(user_id)
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