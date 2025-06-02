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
    
    # 메시지 확인
    messages = state.messages if isinstance(state, AgentState) else state.get('messages', [])
    if not messages:
        return state
        
    # 현재 상태 요약 로깅
    log.info("[Cleanup] Current state summary:")
    if hasattr(state, "summary"):
        log.info(f"  Summary: {state.summary}")
    else:
        log.info("  No summary found in state")
        
    # 정리 전 메시지 로깅
    log.info("[Cleanup] Messages before cleanup:")
    for i, msg in enumerate(state.messages):
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
    last_ai_message = None
    
    # 메시지 순회하며 정리
    for msg in state.messages:
        if isinstance(msg, HumanMessage):
            # 동일한 내용의 HumanMessage가 이미 있는지 확인
            if not any(
                isinstance(m, HumanMessage) and m.content == msg.content 
                for m in cleaned_messages
            ):
                cleaned_messages.append(msg)
        elif isinstance(msg, AIMessage):
            has_tool_calls = (
                hasattr(msg, "additional_kwargs") and 
                "tool_calls" in msg.additional_kwargs
            )
            if not has_tool_calls:
                last_ai_message = msg
                
    # 마지막 AI 메시지 추가
    if last_ai_message:
        cleaned_messages.append(last_ai_message)
    
    # 정리된 메시지로 업데이트
    state.messages = cleaned_messages
    
    # 정리 후 메시지 로깅
    log.info("[Cleanup] Messages after cleanup:")
    for i, msg in enumerate(cleaned_messages):
        msg_type = type(msg).__name__
        msg_content = getattr(msg, 'content', '')
        log.info(f"  [{i}] {msg_type}: {msg_content[:100]}...")
    
    # summarize 체크
    if len(cleaned_messages) > 5:
        state.next_step = "summarize"
        log.info("[Cleanup] Messages count > 5, setting next_step to 'summarize'")
    else:
        state.next_step = "end"
        log.info(f"[Cleanup] Messages count = {len(cleaned_messages)}, setting next_step to 'end'")
    
    return state