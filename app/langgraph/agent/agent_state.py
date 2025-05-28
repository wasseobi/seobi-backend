from typing import Dict, List, Sequence, TypedDict, Union
from langchain_core.messages import BaseMessage

class AgentState(TypedDict):
    """Tool Calling Agent의 상태를 나타내는 타입"""
    messages: List[BaseMessage]  # 대화 히스토리
    current_input: str  # 현재 입력값
    scratchpad: List[BaseMessage]  # Agent의 작업 메모
    next_step: Union[str, None]  # 다음 단계 (계속/종료)
