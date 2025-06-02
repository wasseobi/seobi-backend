"""메시지 포맷 변환 유틸리티."""
import logging
from typing import List, Dict, Any
from langchain_core.messages import BaseMessage, HumanMessage, AIMessage, SystemMessage, ToolMessage

log = logging.getLogger(__name__)

def format_message_content(message: BaseMessage, session_id=None, user_id=None) -> Dict[str, Any]:
    """단일 메시지를 core 필드 중심으로 변환."""
    log.info(f"[Formatter] Processing message of type: {type(message)}")
    
    # 기본 메시지 구조 준비
    formatted_msg = {
        "role": _get_message_role(message),
        "session_id": str(session_id) if session_id else None,
        "user_id": str(user_id) if user_id else None,
        "metadata": None  # 기본값을 None으로 설정
    }
    
    # content 처리
    content = message.content
    if content is None:
        content = ""
    else:
        try:
            if isinstance(content, str):
                content = content.strip()
            else:
                content = str(content)
        except Exception as e:
            log.error(f"[Formatter] Error converting content: {e}")
            content = str(message.content)
    
    formatted_msg["content"] = content
    
    # 메타데이터 처리
    try:
        metadata = {}
        
        log.debug(f"[Formatter] Starting metadata processing for message type: {type(message)}")
        
        if hasattr(message, "additional_kwargs"):
            additional_kwargs = message.additional_kwargs
            log.info(f"[Formatter] Found additional_kwargs: {additional_kwargs}")
            log.info(f"[Formatter] Keys and their types: {[(k, type(k)) for k in additional_kwargs.keys()]}")
            
            # 모든 키-값 쌍을 문자열로 변환하여 저장
            for k, v in additional_kwargs.items():
                str_key = str(k) if not isinstance(k, str) else k
                log.debug(f"[Formatter] Converting key '{k}' ({type(k)}) to string: '{str_key}'")
                metadata[str_key] = v
            
            if "tool_calls" in metadata:
                tool_calls = metadata["tool_calls"]
                log.info(f"[Formatter] Found tool_calls: {tool_calls}")
                for tc in tool_calls:
                    log.debug(f"[Formatter] Tool call keys and their types: {[(k, type(k)) for k in tc.keys()]}")
        
        # 메시지 유형별 특수 처리
        if isinstance(message, AIMessage):
            log.debug("[Formatter] Processing AIMessage specific metadata")
            if "tool_calls" in metadata:
                metadata["type"] = "tool_calls"
                log.info("[Formatter] Set type to tool_calls for AIMessage")
        elif isinstance(message, ToolMessage):
            log.debug("[Formatter] Processing ToolMessage specific metadata")
            metadata["type"] = "tool_response"
            metadata["tool_name"] = message.tool_name if hasattr(message, "tool_name") else None
            metadata["tool_call_id"] = message.tool_call_id if hasattr(message, "tool_call_id") else None
            metadata["original_role"] = "tool"
            
            # Handle function arguments
            if "name" in metadata and "arguments" in metadata:
                metadata["tool_name"] = metadata.pop("name")
                log.info(f"[Formatter] Converted 'name' to 'tool_name' in metadata: {metadata}")
                
        formatted_msg["metadata"] = metadata if metadata and any(metadata.values()) else None
        
    except Exception as e:
        log.error(f"[Formatter] Error processing metadata: {e}")
        formatted_msg["metadata"] = None
        
    return formatted_msg

def format_message_list(messages: List[BaseMessage], session_id=None, user_id=None) -> List[Dict[str, Any]]:
    """메시지 리스트를 포맷팅된 형식으로 변환."""
    formatted_messages = []
    for message in messages:
        formatted_msg = format_message_content(message, session_id, user_id)
        if formatted_msg:
            formatted_messages.append(formatted_msg)
    return formatted_messages

def _get_message_role(message: BaseMessage) -> str:
    """메시지 타입에 따른 역할 반환."""
    if isinstance(message, HumanMessage):
        return "user"
    elif isinstance(message, AIMessage):
        return "assistant"
    elif isinstance(message, SystemMessage):
        return "system"
    elif isinstance(message, ToolMessage):
        return "tool"
    else:
        return "assistant"  # 기본값
