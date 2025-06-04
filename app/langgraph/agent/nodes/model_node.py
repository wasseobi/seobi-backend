"""모델 노드 구현."""
from typing import Dict, Union
import logging
from langchain_core.messages import AIMessage
from app.langgraph.agent.agent_state import AgentState

log = logging.getLogger(__name__)


def model_node(state: Union[Dict, AgentState]) -> Union[Dict, AgentState]:
    """모델 노드 처리"""
    
    # 메시지 로깅
    messages = state["messages"] if isinstance(state, AgentState) else state.get('messages', [])
    if not messages:
        log.warning("[Graph] [model_node] No messages found in state")
        return state
    
    # step_count 처리
    step_count = state["step_count"] if isinstance(state, AgentState) else state.get('step_count', 0)
    step_count += 1
    
    if isinstance(state, AgentState):
        state.step_count = step_count
    else:
        state['step_count'] = step_count
    
    if step_count > 10:
        if isinstance(state, AgentState):
            state.next_step = 'end'
        else:
            state['next_step'] = 'end'
        return state

    try:
        from .call_model import call_model
        result = call_model(state)
        
        result_messages = result.messages if isinstance(result, AgentState) else result.get('messages', [])
        if not result_messages:
            log.warning("[Graph] [model_node] No messages returned from call_model")
            return state

        return result
    except Exception as e:
        log.error(f"[Graph] [model_node] Error: {str(e)}")
        if isinstance(state, AgentState):
            state.error = str(e)
            state.next_step = 'end'
        else:
            state['error'] = str(e)
            state['next_step'] = 'end'
        return state
