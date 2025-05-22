"""그래프의 다음 단계를 결정하는 모듈입니다."""
from langgraph.graph import END

from state import ChatState


def should_continue(state: ChatState) -> str:
    """다음에 실행할 노드를 결정합니다.
    
    현재 상태에 따라 다음 실행할 노드를 결정합니다:
    - action_required가 True이면 "execute_action"으로
    - False이면 END로 이동
    
    Args:
        state (ChatState): 현재 대화 상태

    Returns:
        str: 다음 실행할 노드의 이름 또는 END
    """
    if state["action_required"]:
        return "execute_action"
    return END
