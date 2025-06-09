"""Agent state management."""
from typing import Dict, List, Optional, Union, Any
from dataclasses import dataclass, field
from langchain_core.messages import BaseMessage, HumanMessage, AIMessage, ToolMessage
from app.utils.agent_state_store import AgentStateStore
import logging

log = logging.getLogger(__name__)

@dataclass
class AgentState:
    """Tool Calling Agent의 상태를 나타내는 타입"""
    messages: List[BaseMessage] = field(default_factory=list)
    summary: Optional[str] = None  # 대화 요약
    user_id: Optional[str] = None  # 사용자 식별자
    user_location: Optional[str] = None  # 사용자 위치 정보
    current_input: str = ""  # 현재 입력값
    scratchpad: List[BaseMessage] = field(default_factory=list)  # Agent의 작업 메모
    next_step: Union[str, None] = None  # 다음 단계 (계속/종료)
    user_memory: Optional[str] = None  # 장기 기억(사용자별)
    step_count: int = 0  # 스텝 카운터
    tool_results: Optional[Any] = None  # 도구 실행 결과
    current_tool_call_id: Optional[str] = None  # 현재 실행 중인 도구의 ID
    current_tool_name: Optional[str] = None  # 현재 실행 중인 도구의 이름
    current_tool_calls: Optional[List[Dict]] = None  # 현재 tool_calls 목록

    def __post_init__(self):
        """dataclass 초기화 이후 호출되는 메서드"""
        if self.user_id:
            self.restore_state()

    def restore_state(self):
        """저장된 상태 복원"""
        try:
            saved_state = AgentStateStore.get(self.user_id)
            if saved_state:
                if "messages" in saved_state:
                    # 메시지 타입 검증
                    for msg in saved_state["messages"]:
                        if not isinstance(msg, BaseMessage):
                            raise TypeError("저장된 메시지가 BaseMessage 타입이 아닙니다")
                    self.messages = saved_state["messages"]
                if "summary" in saved_state:
                    self.summary = saved_state["summary"]
        except Exception as e:
            log.error(f"[AgentState] Error restoring state: {str(e)}")
            raise

    def save_state(self):
        """현재 상태 저장"""
        try:
            if not self.user_id:
                log.warning("[AgentState] Attempted to save state without user_id")
                return

            # 메시지 타입 검증
            for msg in self.messages:
                if not isinstance(msg, BaseMessage):
                    log.error(f"[AgentState] Invalid message type: {type(msg)}")
                    raise TypeError("메시지가 BaseMessage 타입이 아닙니다")
                    
            # 전체 상태를 저장
            state_data = self.to_dict()
            AgentStateStore.set(self.user_id, state_data)
        except Exception as e:
            log.error(f"[AgentState] Error saving state: {str(e)}")
            raise

    def to_dict(self) -> Dict:
        """상태를 dict로 변환"""
        result = {
            "messages": self.messages,
            "summary": self.summary,
            "user_id": self.user_id,
            "user_location": self.user_location,
            "current_input": self.current_input,
            "scratchpad": self.scratchpad,
            "next_step": self.next_step,
            "user_memory": self.user_memory,
            "step_count": self.step_count,
            "tool_results": self.tool_results,
            "current_tool_call_id": self.current_tool_call_id,
            "current_tool_name": self.current_tool_name,
            "current_tool_calls": self.current_tool_calls
        }
        return result

    @classmethod
    def from_dict(cls, data: Dict) -> "AgentState":
        """dict에서 새로운 AgentState 인스턴스 생성"""
        return cls(**data)

    def __getitem__(self, key: str) -> Any:
        """Dict-like 접근 지원"""
        try:
            return getattr(self, key)
        except AttributeError:
            raise KeyError(key)

    def __setitem__(self, key: str, value: Any) -> None:
        """Dict-like 설정 지원"""
        setattr(self, key, value)

    def get(self, key: str, default: Any = None) -> Any:
        """Dict-like get 메서드 지원"""
        try:
            return getattr(self, key, default)
        except AttributeError:
            return default

    def set_tool_info(self, tool_calls: List[Dict]) -> None:
        """도구 실행 정보 설정"""
        self.current_tool_calls = tool_calls
        if tool_calls and len(tool_calls) > 0:
            first_tool = tool_calls[0]
            self.current_tool_call_id = first_tool.get("id")
            self.current_tool_name = first_tool.get("function", {}).get("name")

    def set_tool_results(self, results: Any) -> None:
        """도구 실행 결과 설정"""
        self.tool_results = results

    def clear_tool_state(self) -> None:
        """도구 관련 상태 초기화"""
        self.tool_results = None
        self.current_tool_call_id = None
        self.current_tool_name = None
        self.current_tool_calls = None

    def validate_messages(self) -> bool:
        """메시지 순서와 패턴이 올바른지 검증
        - user와 assistant 메시지가 번갈아가며 있어야 함
        - tool 메시지는 assistant의 tool_calls 이후에만 올 수 있음
        """
        if not self.messages:
            return True

        for i in range(len(self.messages) - 1):
            curr = self.messages[i]
            next_msg = self.messages[i + 1]
            
            # Human -> AI 또는 AI(tool_calls) -> Tool -> AI 패턴 검증
            if isinstance(curr, HumanMessage):
                if not isinstance(next_msg, AIMessage):
                    log.warning(f"Invalid message pattern: Human message should be followed by AI message")
                    return False
            elif isinstance(curr, AIMessage):
                if isinstance(next_msg, HumanMessage):
                    continue
                elif isinstance(next_msg, ToolMessage):
                    # tool_calls가 있는 AI 메시지 다음에만 Tool 메시지 허용
                    if not (hasattr(curr, "additional_kwargs") and "tool_calls" in curr.additional_kwargs):
                        log.warning(f"Tool message without preceding AI tool_calls")
                        return False
                else:
                    log.warning(f"Invalid message pattern after AI message")
                    return False
            elif isinstance(curr, ToolMessage):
                if not isinstance(next_msg, AIMessage):
                    log.warning(f"Tool message should be followed by AI message")
                    return False

        return True
