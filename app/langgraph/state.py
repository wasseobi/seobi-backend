"""대화 상태를 관리하는 모듈입니다."""
from typing import Dict, List, Any, Union
from datetime import datetime
from dataclasses import dataclass, field
from langchain.schema import BaseMessage


@dataclass
class ChatState:
    """대화 상태를 관리하는 클래스입니다."""

    # 필수 필드
    user_input: str = ""
    parsed_intent: Dict = field(default_factory=dict)
    reply: str = ""
    action_required: bool = False
    executed_result: Dict = field(default_factory=dict)
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())
    user_id: str = ""
    messages: List[BaseMessage] = field(default_factory=list)

    VALID_KEYS = [
        "user_input",
        "parsed_intent",
        "reply",
        "action_required",
        "executed_result",
        "timestamp",
        "user_id",
        "messages"
    ]

    def __post_init__(self):
        """dataclass 초기화 후 처리"""
        if self.parsed_intent is None:
            self.parsed_intent = {}
        if self.executed_result is None:
            self.executed_result = {}
        if self.messages is None:
            self.messages = []

    @staticmethod
    def merge_states(states: List[Dict]) -> Dict:
        """여러 상태를 하나로 병합합니다."""
        if not states:
            return {}
        merged = {}
        for state in states:
            if isinstance(state, dict):
                merged.update(state)
        return merged

    def __getitem__(self, key: Union[str, int]) -> Any:
        """상태 값을 조회합니다."""
        # messages 리스트에 대한 인덱스 접근 처리
        if isinstance(key, int):
            if not isinstance(self.messages, (list, tuple)):
                raise TypeError("messages가 리스트가 아닙니다")
            try:
                return self.messages[key]
            except IndexError:
                raise IndexError(f"messages 인덱스 범위 초과: {key}")

        # 문자열 키에 대한 기존 처리
        if not isinstance(key, str):
            import traceback
            traceback.print_stack()
            raise TypeError(f"키는 문자열이어야 합니다. (입력값: {key!r}, 타입: {type(key)})")

        if key not in self.VALID_KEYS:
            raise KeyError(f"존재하지 않는 키입니다: {key}")
        return getattr(self, key)

    def get(self, key: Union[str, int], default: Any = None) -> Any:
        """안전하게 상태 값을 조회합니다."""
        try:
            return self[key]
        except (KeyError, TypeError, IndexError):
            return default

    @property
    def keys(self) -> List[str]:
        """유효한 키 목록을 반환합니다."""
        return self.VALID_KEYS.copy()

    @classmethod
    def from_dict(cls, data: Dict) -> 'ChatState':
        """딕셔너리로부터 ChatState 인스턴스를 생성합니다."""
        if isinstance(data, list):
            data = cls.merge_states(data)
        return cls(**{k: v for k, v in data.items() if k in cls.VALID_KEYS})

    def to_dict(self) -> Dict:
        """ChatState 인스턴스를 딕셔너리로 변환합니다."""
        return {k: getattr(self, k) for k in self.VALID_KEYS}
