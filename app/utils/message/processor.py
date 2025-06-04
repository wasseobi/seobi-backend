"""메시지 처리기 클래스."""
from typing import Dict, List, Any, Generator, Union, Set
from langchain_core.messages import BaseMessage, AIMessage, ToolMessage, HumanMessage
import json

from app.dao.message_dao import MessageDAO
from app.utils.message.formatter import format_message_content

class MessageProcessor:
    def __init__(self, session_id: str, user_id: str):
        self.dao = MessageDAO()
        self.session_info = {
            "session_id": session_id,
            "user_id": user_id
        }
        self.seen_messages: Set[str] = set()

    def process_agent_messages(self, messages_to_process: List[Dict]) -> Generator[str, None, None]:
        """에이전트 메시지 처리."""
        for msg in messages_to_process:
            if not isinstance(msg, dict):
                continue
                
            msg_content = msg.get("content", "").strip()
            msg_metadata = msg.get("metadata", {}) or {}
            
            if not (msg_content or msg_metadata):
                continue
                
            formatted_msg = self._format_message(msg_content, msg_metadata, msg.get("role", "assistant"))
            yield from self._save_and_yield_message(formatted_msg)

    def process_ai_or_tool_message(self, chunk: Union[AIMessage, ToolMessage]) -> Generator[str, None, None]:
        """AI 또는 Tool 메시지 처리."""
        formatted_msg = format_message_content(chunk, **self.session_info)
        msg_key = self._get_message_key(formatted_msg)
        
        if msg_key not in self.seen_messages:
            self.seen_messages.add(msg_key)
            yield f"data: {json.dumps(formatted_msg, ensure_ascii=False)}\n\n"

    def process_dict_message(self, chunk: Dict) -> Generator[str, None, None]:
        """Dict 형태의 메시지 처리."""
        content = chunk.get("content", "").strip()
        metadata = chunk.get("metadata", {}) or {}
        formatted_msg = self._format_message(content, metadata, chunk.get("role", "assistant"))
        yield from self._save_and_yield_message(formatted_msg)

    def process_error(self, error: Exception) -> Generator[str, None, None]:
        """에러 메시지 처리."""
        error_msg = {
            "content": f"죄송합니다. 응답을 생성하는 동안 오류가 발생했습니다. ({str(error)})",
            "role": "assistant",
            "metadata": {"error": str(error)},
            **self.session_info
        }
        yield from self._save_and_yield_message(error_msg)

    def _format_message(self, content: str, metadata: Dict, default_role: str = "assistant") -> Dict:
        """메시지 포맷팅."""
        role = default_role
        if metadata.get("type") == "tool_response" or \
           (metadata.get("tool_name") and not "tool_calls" in metadata) or \
           metadata.get("original_role") == "tool":
            role = "tool"
        elif "tool_calls" in metadata:
            role = "assistant"
            
        return {
            "content": content,
            "role": role,
            "metadata": metadata if metadata and any(metadata.values()) else None,
            **self.session_info
        }

    def _save_and_yield_message(self, formatted_msg: Dict) -> Generator[str, None, None]:
        """메시지 저장 및 yield."""
        msg_key = self._get_message_key(formatted_msg)
        if msg_key in self.seen_messages:
            return
            
        self.seen_messages.add(msg_key)
        
        saved_message = self.dao.create(
            session_id=self.session_info["session_id"],
            user_id=self.session_info["user_id"],
            content=formatted_msg["content"],
            role=formatted_msg["role"],
            metadata=formatted_msg["metadata"]
        )
        yield f"data: {json.dumps(formatted_msg, ensure_ascii=False)}\n\n"

    def _get_message_key(self, msg: Dict[str, Any]) -> str:
        """메시지의 고유 키를 생성하는 함수"""
        metadata = msg.get("metadata", {})
        if metadata and msg.get("role") == "tool":
            tool_call_id = metadata.get("tool_call_id")
            if tool_call_id:
                return f"tool_{tool_call_id}"
                
        content = msg.get("content", "").strip()
        role = msg.get("role", "")
        if content and role:
            return f"{role}_{hash(content)}"
            
        if metadata:
            return f"{role}_{hash(str(metadata))}"
            
        return f"{role}_{hash(content)}_{hash(str(metadata))}"
