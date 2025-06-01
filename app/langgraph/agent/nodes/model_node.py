"""모델 노드 구현."""
from typing import Dict
from langchain_core.messages import AIMessage
from app.langgraph.agent.agent_state import AgentState


def model_node(state: AgentState) -> AgentState:
    print(f"[Graph] [model_node] state in: {state}")
    if "step_count" not in state:
        state["step_count"] = 0
    state["step_count"] += 1

    if state["step_count"] > 10:
        state["next_step"] = "end"
        print(f"[Graph] [model_node] step_count limit, state out: {state}")
        return state

    try:
        from .call_model import call_model
        result = call_model(state)
        print(f"[Graph] [model_node] state out: {result}")
        return result
    except Exception as e:
        print(f"[Graph] [model_node] Error: {str(e)}")
        state["next_step"] = "end"  # 에러 발생 시 종료
        return state
