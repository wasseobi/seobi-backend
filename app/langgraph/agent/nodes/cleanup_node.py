"""대화 종료 전 메시지 정리 모듈."""
from typing import Dict, Union
import logging
from langchain_core.messages import AIMessage, HumanMessage, ToolMessage
from ..agent_state import AgentState

# cleanup 로거 설정
log = logging.getLogger("langgraph_debug")

def cleanup_node(state: Union[Dict, AgentState]) -> Union[Dict, AgentState]:
    """대화 종료 전 메시지 정리."""
    log.info(f"[Cleanup] Input state type: {type(state)}")
    
    # state가 dict인지 AgentState인지 확인
    is_dict = isinstance(state, dict)
    
    # 메시지 확인
    messages = state.get('messages', []) if is_dict else state.messages
    if not messages:
        return state
        
    # 현재 상태 요약 로깅
    log.info("[Cleanup] Current state summary:")
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
        
    # 정리 전 메시지 로깅
    log.info("[Cleanup] Messages before cleanup:")
    for i, msg in enumerate(messages):
        msg_type = type(msg).__name__
        msg_content = getattr(msg, 'content', '')
        has_tool_calls = False
        
        if isinstance(msg, AIMessage):
            has_tool_calls = (
                hasattr(msg, "additional_kwargs") and 
                "tool_calls" in msg.additional_kwargs
            )
            
        log.info(f"  [{i}] {msg_type}" + 
                (f" (with tool_calls)" if has_tool_calls else "") +
                f": {msg_content[:100]}...")
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
    
    # 정리 후 메시지 로깅
    log.info("[Cleanup] Messages after cleanup:")
    for i, msg in enumerate(cleaned_messages):
        msg_type = type(msg).__name__
        msg_content = getattr(msg, 'content', '')
        log.info(f"  [{i}] {msg_type}: {msg_content[:100]}...")
    
    # summarize 체크
    if len(cleaned_messages) > 5:
        if is_dict:
            state["next_step"] = "summarize"
        else:
            state.next_step = "summarize"
        log.info("[Cleanup] Messages count > 5, setting next_step to 'summarize'")
    else:
        if is_dict:
            state["next_step"] = "end"
        else:
            state.next_step = "end"
        log.info(f"[Cleanup] Messages count = {len(cleaned_messages)}, setting next_step to 'end'")
    
    return state