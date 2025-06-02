"""모델 노드 구현."""
from typing import Dict, Union
import logging
from langchain_core.messages import AIMessage
from app.langgraph.agent.agent_state import AgentState

log = logging.getLogger("langgraph_debug")


def model_node(state: Union[Dict, AgentState]) -> Union[Dict, AgentState]:
    """모델 노드 처리"""
    log.info(f"[Graph] [model_node] State type: {type(state)}")
    log.info("[Graph] [model_node] State before processing:")
    
    # 메시지 로깅
    messages = state.messages if isinstance(state, AgentState) else state.get('messages', [])
    for i, msg in enumerate(messages):
        log.info(f"  Message [{i}]: {type(msg).__name__} - {getattr(msg, 'content', '')[:100]}...")

    # step_count 처리
    step_count = state.step_count if isinstance(state, AgentState) else state.get('step_count', 0)
    step_count += 1
    
    if isinstance(state, AgentState):
        state.step_count = step_count
    else:
        state['step_count'] = step_count
    
    log.info(f"[Graph] [model_node] Current step count: {step_count}")

    if step_count > 10:
        if isinstance(state, AgentState):
            state.next_step = 'end'
        else:
            state['next_step'] = 'end'
        log.info("[Graph] [model_node] step_count limit reached")
        return state

    try:
        from .call_model import call_model
        result = call_model(state)
        
        # 결과 로깅
        log.info("[Graph] [model_node] State after processing:")
        result_messages = result.messages if isinstance(result, AgentState) else result.get('messages', [])
        for i, msg in enumerate(result_messages):
            log.info(f"  Message [{i}]: {type(msg).__name__} - {getattr(msg, 'content', '')[:100]}...")
        
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
