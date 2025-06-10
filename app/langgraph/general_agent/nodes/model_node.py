"""모델 노드 구현 (MCP + 직접 구현 도구 통합)."""
from typing import Dict, Union
import logging
from langchain_core.messages import AIMessage
from app.langgraph.general_agent.agent_state import AgentState

log = logging.getLogger(__name__)


def model_node(state: Union[Dict, AgentState]) -> Union[Dict, AgentState]:
    """모델 노드 처리 (MCP + 직접 구현 도구 통합)"""
    
    # 메시지 로깅
    messages = state.get('messages', []) if isinstance(state, dict) else getattr(state, 'messages', [])
    
    # 디버깅을 위한 상세 로깅
    log.info(f"[model_node] State type: {type(state)}")
    log.info(f"[model_node] Messages: {messages}")
    log.info(f"[model_node] Messages length: {len(messages) if messages else 0}")
    log.info(f"[model_node] Messages type: {type(messages)}")
    
    if not messages:
        log.warning("[Graph] [model_node] No messages found in state")
        log.warning(f"[Graph] [model_node] State keys: {state.keys() if isinstance(state, dict) else 'AgentState'}")
        
        # 메시지가 없으면 기본 응답 생성
        if isinstance(state, dict):
            state['messages'] = [AIMessage(content="안녕하세요! 무엇을 도와드릴까요?")]
            state['next_step'] = 'cleanup'
        else:
            state.messages = [AIMessage(content="안녕하세요! 무엇을 도와드릴까요?")]
            state.next_step = 'cleanup'
        return state
    
    # step_count 처리
    step_count = state.get('step_count', 0) if isinstance(state, dict) else getattr(state, 'step_count', 0)
    step_count += 1
    
    if isinstance(state, dict):
        state['step_count'] = step_count
    else:
        state.step_count = step_count
    
    if step_count > 10:
        if isinstance(state, dict):
            state['next_step'] = 'cleanup'
        else:
            state.next_step = 'cleanup'
        return state

    try:
        from .call_model import call_model
        result = call_model(state)
        
        result_messages = result.get('messages', []) if isinstance(result, dict) else getattr(result, 'messages', [])
        if not result_messages:
            log.warning("[Graph] [model_node] No messages returned from call_model")
            return state

        return result
    except Exception as e:
        log.error(f"[Graph] [model_node] Error: {str(e)}")
        if isinstance(state, dict):
            state['error'] = str(e)
            state['next_step'] = 'cleanup'
        else:
            state.error = str(e)
            state.next_step = 'cleanup'
        return state 