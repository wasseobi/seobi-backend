"""메시지 포맷 변환 유틸리티."""
import logging
from typing import List, Dict, Any
from langchain_core.messages import BaseMessage, HumanMessage, AIMessage, SystemMessage, ToolMessage

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

def format_message_content(message: BaseMessage, session_id=None, user_id=None) -> Dict[str, Any]:
    """단일 메시지를 core 필드 중심으로 변환."""
    logger.debug(f"\n=== Message Formatting Start ===")
    logger.debug(f"Input message type: {type(message)}")
    logger.debug(f"Input message content: {message.content}")
    logger.debug(f"Input message kwargs: {message.additional_kwargs if hasattr(message, 'additional_kwargs') else None}")
    logger.debug(f"Session ID: {session_id}, User ID: {user_id}")
    
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
            logger.error(f"Error processing content: {e}")
            content = str(message.content)
    
    formatted_msg["content"] = content
    
    # 메타데이터 처리
    try:
        metadata = {}
        if hasattr(message, "additional_kwargs"):
            metadata.update(message.additional_kwargs)
        
        # 메시지 유형별 특수 처리
        if isinstance(message, AIMessage):
            if "tool_calls" in metadata:
                metadata["type"] = "tool_calls"
        elif isinstance(message, ToolMessage):
            # tool 메시지 속성 보존
            tool_metadata = {
                "type": "tool_response",
                "tool_call_id": getattr(message, "tool_call_id", None),
                "tool_name": getattr(message, "name", None),
                "original_role": "tool"
            }
            metadata.update(tool_metadata)
            formatted_msg["role"] = "tool"
            
            if not content and (tool_metadata["tool_name"] or tool_metadata["tool_call_id"]):
                content = f"Tool execution: {tool_metadata['tool_name'] or tool_metadata['tool_call_id']}"
                formatted_msg["content"] = content
                
        # 메타데이터가 실제 값을 가지고 있는 경우에만 설정
        formatted_msg["metadata"] = metadata if metadata and any(v is not None for v in metadata.values()) else None
            
    except Exception as e:
        logger.error(f"Error processing metadata: {e}")
        formatted_msg["metadata"] = None
    
    logger.debug(f"=== Formatted Message ===")
    logger.debug(f"Content: {formatted_msg['content']}")
    logger.debug(f"Role: {formatted_msg['role']}")
    logger.debug(f"Metadata: {formatted_msg['metadata']}")
    logger.debug(f"Session/User IDs: {formatted_msg['session_id']}, {formatted_msg['user_id']}")
    logger.debug("=== Message Formatting End ===")
    
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
