"""메시지 컨텍스트를 관리하는 클래스입니다."""
from datetime import datetime, timezone
from typing import List, Dict, Any, Optional
from dataclasses import dataclass, field
import json
import logging

log = logging.getLogger(__name__)


def datetime_to_str(obj: Any) -> Any:
    """datetime 객체를 ISO 형식 문자열로 변환합니다."""
    if isinstance(obj, datetime):
        try:
            return obj.isoformat()
        except Exception as e:
            log.error(f"Error converting datetime to string: {e}")
            return str(obj)
    elif isinstance(obj, dict):
        return {k: datetime_to_str(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [datetime_to_str(item) for item in obj]
    return obj


@dataclass
class MessageContext:
    """대화 진행 중의 메시지와 메타데이터를 임시로 저장하는 클래스입니다."""

    session_id: str
    user_id: str
    messages: List[Dict[str, Any]] = field(default_factory=list)
    final_content: str = ""
    current_tool_call_chunks: List[Dict[str, Any]] = field(default_factory=list)

    def _create_message(self, role: str, content: str, metadata: Optional[Dict] = None) -> Dict[str, Any]:
        """메시지 객체를 생성합니다."""
        message = {
            "role": role,
            "content": content,
            "timestamp": datetime.now(timezone.utc)
        }
        if metadata:
            message["metadata"] = metadata
            if "timestamp" not in metadata:
                message["metadata"]["timestamp"] = message["timestamp"]
        return message

    def add_user_message(self, content: str) -> None:
        """사용자 메시지를 추가합니다."""
        message = self._create_message("user", content)
        log.debug(f"Adding user message: {message}")
        self.messages.append(message)

    def combine_tool_call_chunks(self) -> Optional[Dict[str, Any]]:
        """도구 호출 청크들을 하나의 완성된 도구 호출로 합칩니다."""
        if not self.current_tool_call_chunks:
            return None

        # 첫 번째 청크에서 기본 구조 가져오기
        combined = self.current_tool_call_chunks[0].copy()

        # arguments 문자열 합치기
        arguments = ""
        for chunk in self.current_tool_call_chunks:
            if chunk.get("function", {}).get("arguments"):
                arguments += chunk["function"]["arguments"]

        # 완성된 도구 호출 생성
        if combined.get("function"):
            combined["function"]["arguments"] = arguments

        return combined

    def add_tool_call_chunk(self, chunk: Dict[str, Any]) -> None:
        """도구 호출 청크를 추가합니다."""
        if chunk.get("id"):
            self.flush_tool_call_chunks()
            log.debug(f"Starting new tool call with chunk: {chunk}")
            self.current_tool_call_chunks = [chunk]
        else:
            log.debug(f"Appending tool call chunk: {chunk}")
            self.current_tool_call_chunks.append(chunk)

    def flush_tool_call_chunks(self) -> None:
        """현재 도구 호출 청크들을 처리하고 메시지로 저장합니다."""
        if not self.current_tool_call_chunks:
            return

        combined_tool_call = self.combine_tool_call_chunks()
        if combined_tool_call:
            message = self._create_message(
                role="assistant",
                content="",
                metadata={"tool_calls": [combined_tool_call]}
            )
            log.debug(f"Adding combined tool call message: {message}")
            self.messages.append(message)

        self.current_tool_call_chunks = []

    def add_tool_result(self, tool_name: str, result: Any) -> None:
        """도구 실행 결과를 추가합니다."""
        message = self._create_message(
            role="tool",
            content=str(result),
            metadata={
                "tool_name": tool_name,
                "result": result
            }
        )
        log.debug(f"Adding tool result message: {message}")
        self.messages.append(message)

    def append_assistant_content(self, content: str) -> None:
        """AI 응답 청크를 누적합니다."""
        self.final_content += content
        log.debug(f"Appended content, current final_content length: {len(self.final_content)}")

    def finalize_assistant_response(self) -> None:
        """완성된 AI 응답을 메시지에 추가합니다."""
        self.flush_tool_call_chunks()

        tools_used = [
            msg["metadata"]["tool_calls"][0]
            for msg in self.messages
            if msg["role"] == "assistant" and "tool_calls" in msg.get("metadata", {})
        ]

        message = self._create_message(
            role="assistant",
            content=self.final_content,
            metadata={"tools_used": tools_used}
        )
        log.debug(f"Adding final assistant response: {message}")
        self.messages.append(message)

    def get_messages_for_storage(self) -> List[Dict[str, Any]]:
        """저장할 메시지 목록을 반환합니다."""
        log.info(f"Preparing {len(self.messages)} messages for storage")

        formatted_messages = []
        for msg in self.messages:
            formatted_msg = msg.copy()
            # timestamp가 메타데이터에도 있고 메시지 루트에도 있으면 중복 제거
            if "timestamp" in formatted_msg and "metadata" in formatted_msg:
                if "timestamp" in formatted_msg["metadata"]:
                    del formatted_msg["metadata"]["timestamp"]
            formatted_messages.append(formatted_msg)

        return datetime_to_str(formatted_messages)
