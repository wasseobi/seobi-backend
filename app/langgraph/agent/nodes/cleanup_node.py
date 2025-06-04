"""대화 종료 전 메시지 정리 모듈."""
from typing import Dict, Union
import logging
from langchain_core.messages import AIMessage, HumanMessage, ToolMessage
from ..agent_state import AgentState

# cleanup 로거 설정
log = logging.getLogger(__name__)

def cleanup_node(state: Union[Dict, AgentState]) -> Union[Dict, AgentState]:
    """대화 종료 전 메시지 정리."""
    
    # state가 dict인지 AgentState인지 확인
    is_dict = isinstance(state, dict)
    
    # 메시지 확인
    messages = state.get('messages', []) if is_dict else state.messages
    if not messages:
        return state
        
    # 현재 상태 요약 로깅
    if is_dict:
        summary = state.get("summary")
        if summary:
            log.info(f"  Summary: {summary}")
        else:
            log.info("  No summary found in state")
    else:
        if hasattr(state, "summary"):
            log.info(f"  Summary: {state.summary}")
        else:
            log.info("  No summary found in state")
        
    for i, msg in enumerate(messages):
        msg_type = type(msg).__name__
        msg_content = getattr(msg, 'content', '')
        has_tool_calls = False
        
        if isinstance(msg, AIMessage):
            has_tool_calls = (
                hasattr(msg, "additional_kwargs") and 
                "tool_calls" in msg.additional_kwargs
            )
            
    cleaned_messages = []
    current_human_message = None
    current_ai_response = None
    
    # 메시지 순회하며 정리
    for msg in messages:
        if isinstance(msg, HumanMessage):
            # 이전 대화 쌍이 있으면 저장
            if current_human_message and current_ai_response:
                cleaned_messages.append(current_human_message)
                cleaned_messages.append(current_ai_response)
            current_human_message = msg
            current_ai_response = None
        elif isinstance(msg, AIMessage):
            has_tool_calls = (
                hasattr(msg, "additional_kwargs") and 
                "tool_calls" in msg.additional_kwargs
            )
            # tool_calls가 없는 AIMessage만 최종 응답으로 저장
            if not has_tool_calls:
                current_ai_response = msg

    # 마지막 대화 쌍 처리
    if current_human_message and current_ai_response:
        cleaned_messages.append(current_human_message)
        cleaned_messages.append(current_ai_response)
    
    # 정리된 메시지로 업데이트
    if is_dict:
        state["messages"] = cleaned_messages
    else:
        state.messages = cleaned_messages
    
    for i, msg in enumerate(cleaned_messages):
        msg_type = type(msg).__name__
        msg_content = getattr(msg, 'content', '')

    state["step_count"] = 0
    
    # summarize 체크
    if len(cleaned_messages) > 5:
        if is_dict:
            state["next_step"] = "summarize"
        else:
            state.next_step = "summarize"
    else:
        if is_dict:
            state["next_step"] = "end"
        else:
            state.next_step = "end"
    
    return state