"""의도 분석 결과를 바탕으로 다음 단계를 결정하는 모듈입니다."""
from typing import Dict, Any
from app.langgraph.state import ChatState

def task_decision(state: Dict[str, Any]) -> Dict[str, Any]:
    """의도 분석 결과를 바탕으로 다음 단계를 결정합니다."""
    state = ChatState.from_dict(state) if isinstance(state, (list, dict)) else state
    parsed_intent = state.get("parsed_intent", {})
    
    # 의도가 없는 경우 기본값 설정
    if not parsed_intent:
        parsed_intent = {"intent": "general_chat", "params": {}}
        
    intent = parsed_intent.get("intent", "general_chat")
    action_required = intent != "general_chat"
    
    # 상태 업데이트
    return {**state.to_dict(), "action_required": action_required}
