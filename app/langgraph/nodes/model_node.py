"""모델 노드 구현."""
from typing import Dict
from langchain_core.messages import AIMessage

def model_node(state: Dict) -> Dict:
    """에이전트 노드: LLM을 호출하고 다음 상태를 결정"""
    if "step_count" not in state:
        state["step_count"] = 0
    state["step_count"] += 1
    
    if state["step_count"] > 10:  # 최대 10단계로 제한
        state["next_step"] = "end"
        return state
        
    # call_model 함수 호출
    from .call_model import call_model
    result = call_model(state)
    return result
