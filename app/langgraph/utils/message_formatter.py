"""메시지 포맷 변환 유틸리티."""
import logging
from typing import List, Dict, Any
from langchain_core.messages import BaseMessage, HumanMessage, AIMessage, SystemMessage, ToolMessage

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

def format_message_content(message: BaseMessage, session_id=None, user_id=None) -> Dict[str, Any]:
    """단일 메시지를 core 필드 중심으로 변환.
    
    Args:
        message: LangChain BaseMessage 객체
        session_id: 세션 ID
        user_id: 사용자 ID
        
    Returns:
        role, content, metadata가 포함된 딕셔너리
    """
    logger.debug(f"Formatting message: type={type(message)}, content={message.content}")
    
    content = message.content
    # 문자열인 경우에만 디코딩 처리
    if isinstance(content, str):
        try:
            content_bytes = content.encode('utf-8')
            content = content_bytes.decode('utf-8')
            logger.debug(f"Decoded content during formatting: {content}")
        except UnicodeError as e:
            logger.error(f"Unicode error during content formatting: {e}")
            content = message.content
    
    # 기본 메시지 구조
    formatted_msg = {
        "content": content,
        "role": _get_message_role(message),
        "metadata": message.additional_kwargs if hasattr(message, "additional_kwargs") else {},
        "session_id": str(session_id) if session_id else None,
        "user_id": str(user_id) if user_id else None
    }
    
    # 메타데이터 처리
    if isinstance(message, AIMessage):
        if "tool_calls" in formatted_msg["metadata"]:
            formatted_msg["metadata"]["type"] = "tool_calls"
    
    elif isinstance(message, ToolMessage):
        tool_metadata = {
            "type": "tool_response",
            "tool_call_id": getattr(message, "tool_call_id", None),
            "tool_name": getattr(message, "name", None)
        }
        formatted_msg["metadata"].update(tool_metadata)

    # 빈 메타데이터는 None으로 설정
    if not formatted_msg["metadata"]:
        formatted_msg["metadata"] = None
    
    logger.debug(f"Formatted message: {formatted_msg}")
    return formatted_msg

def format_message_list(messages: List[BaseMessage], session_id=None, user_id=None) -> List[Dict[str, Any]]:
    """메시지 리스트를 변환 및 저장.
    
    Args:
        messages: LangChain BaseMessage 객체 리스트
        session_id: 세션 ID
        user_id: 사용자 ID
        
    Returns:
        변환된 메시지 딕셔너리 리스트
    """
    return [format_message_content(msg, session_id=session_id, user_id=user_id) for msg in messages]

def _get_message_role(message: BaseMessage) -> str:
    """메시지 타입에 따른 role 값 반환"""
    if isinstance(message, HumanMessage):
        return "user"
    elif isinstance(message, AIMessage):
        return "assistant"
    elif isinstance(message, SystemMessage):
        return "system"
    elif isinstance(message, ToolMessage):
        return "tool"
    else:
        return "user"  # 기본값
