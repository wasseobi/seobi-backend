"""대화 상태를 관리하는 모듈입니다."""
from typing import Dict, Optional, List, Any
from datetime import datetime
from dataclasses import dataclass, field

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
    messages: List = field(default_factory=list)
    
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

    def __getitem__(self, key: str) -> Any:
        """상태 값을 조회합니다."""
        if not isinstance(key, str):
            import traceback
            print(f"[ChatState] 잘못된 key 접근: {key!r} (type: {type(key)})")
            print(f"[ChatState] 현재 keys: {self.VALID_KEYS}")
            print("[ChatState] 스택 트레이스:")
            traceback.print_stack()
            raise TypeError(f"키는 문자열이어야 합니다. (입력값: {key!r}, 타입: {type(key)})")
        if key not in self.VALID_KEYS:
            raise KeyError(f"존재하지 않는 키입니다: {key}")
        return getattr(self, key)

    def __setitem__(self, key: str, value: Any) -> None:
        """상태 값을 설정합니다."""
        if not isinstance(key, str):
            raise TypeError(f"키는 문자열이어야 합니다. (입력값: {key!r}, 타입: {type(key)})")
        if key not in self.VALID_KEYS:
            raise KeyError(f"존재하지 않는 키입니다: {key}")
        setattr(self, key, value)

    def get(self, key: str, default: Any = None) -> Any:
        """안전하게 상태 값을 조회합니다."""
        try:
            return self[key]
        except (KeyError, TypeError):
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
