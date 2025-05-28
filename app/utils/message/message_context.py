"""메시지 컨텍스트를 관리하는 클래스입니다."""
from datetime import datetime, timezone
from typing import List, Dict, Any, Optional
from dataclasses import dataclass, field
import json
import logging

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

def datetime_to_str(obj: Any) -> Any:
    """datetime 객체를 ISO 형식 문자열로 변환합니다.
    timezone 정보를 포함한 형식: YYYY-MM-DD HH:MM:SS.mmmmmm+HH:MM
    """
    if isinstance(obj, datetime):
        try:
            # timezone 정보를 포함한 형식으로 변환
            return obj.strftime('%Y-%m-%d %H:%M:%S.%f%z')
        except Exception as e:
            logger.error(f"Datetime 변환 오류: {str(e)}")
            # fallback: 기본 ISO 형식
            return obj.isoformat()
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
    
    def add_user_message(self, content: str) -> None:
        """사용자 메시지를 추가합니다."""
        message = {
            "role": "user",
            "content": content,
            "timestamp": datetime.now(timezone.utc)
        }
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
        # 새로운 도구 호출의 시작
        if chunk.get("id"):
            self.flush_tool_call_chunks()  # 이전 청크들 처리
            self.current_tool_call_chunks = [chunk]
        else:
            self.current_tool_call_chunks.append(chunk)
    
    def flush_tool_call_chunks(self) -> None:
        """현재 도구 호출 청크들을 처리하고 메시지로 저장합니다."""
        if not self.current_tool_call_chunks:
            return
            
        combined_tool_call = self.combine_tool_call_chunks()
        if combined_tool_call:
            message = {
                "role": "assistant",
                "content": "",
                "metadata": {
                    "tool_calls": [combined_tool_call],
                    "timestamp": datetime.now(timezone.utc)
                }
            }
            self.messages.append(message)
        
        self.current_tool_call_chunks = []
    
    def add_tool_result(self, tool_name: str, result: Any) -> None:
        """도구 실행 결과를 추가합니다."""
        message = {
            "role": "tool",
            "content": str(result),
            "metadata": {
                "tool_name": tool_name,
                "result": result,
                "timestamp": datetime.now(timezone.utc)
            }
        }
        self.messages.append(message)
        # logger.debug(f"도구 실행 결과 추가: {json.dumps(datetime_to_str(message))}")
    
    def append_assistant_content(self, content: str) -> None:
        """AI 응답 청크를 누적합니다."""
        self.final_content += content
        # logger.debug(f"AI 응답 청크 추가 (현재 길이: {len(self.final_content)})")
    
    def finalize_assistant_response(self) -> None:
        """완성된 AI 응답을 메시지에 추가합니다."""
        # 남아있는 도구 호출 청크 처리
        self.flush_tool_call_chunks()
        
        tools_used = [
            msg["metadata"]["tool_calls"][0]
            for msg in self.messages
            if msg["role"] == "assistant" and "tool_calls" in msg.get("metadata", {})
        ]
        
        message = {
            "role": "assistant",
            "content": self.final_content,
            "metadata": {
                "tools_used": tools_used,
                "timestamp": datetime.now(timezone.utc)
            }
        }
        self.messages.append(message)
    
    def get_messages_for_storage(self) -> List[Dict[str, Any]]:
        """저장할 메시지 목록을 반환합니다. datetime 객체를 문자열로 변환합니다."""
        return datetime_to_str(self.messages)
