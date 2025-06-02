"""메시지 변환 유틸리티."""
import logging
from typing import List, Dict, Any
from langchain_core.messages import BaseMessage, HumanMessage, AIMessage, SystemMessage, ToolMessage

log = logging.getLogger(__name__)

def convert_to_openai_messages(messages: List[BaseMessage]) -> List[Dict[str, Any]]:
    """LangChain 메시지를 OpenAI 형식으로 변환.
    
    Args:
        messages: LangChain BaseMessage 객체 리스트
        
    Returns:
        OpenAI 메시지 형식의 딕셔너리 리스트
    """
    log.info(f"[Converter] Converting {len(messages)} messages to OpenAI format")
    openai_messages = []
    last_assistant_message = None
    
    for idx, message in enumerate(messages):
        log.debug(f"[Converter] Processing message {idx} of type: {type(message)}")
        # 기본 메시지 구조
        msg_dict = {
            "content": message.content
        }
        
        # 역할 설정
        msg_dict["role"] = _get_role(message)
        
        # ToolMessage 특수 처리
        if isinstance(message, ToolMessage):
            log.info(f"[Converter] Processing ToolMessage: {message}")
            msg_dict["role"] = "tool"  # 항상 tool role 유지
            
            # tool_call_id 처리
            tool_call_id = None
            if hasattr(message, "tool_call_id"):
                tool_call_id = message.tool_call_id
                log.debug(f"[Converter] Found tool_call_id in message: {tool_call_id}")
            elif last_assistant_message and "tool_calls" in last_assistant_message.get("additional_kwargs", {}):
                tool_call = last_assistant_message["additional_kwargs"]["tool_calls"][0]
                tool_call_id = tool_call.get("id")
                log.debug(f"[Converter] Inferred tool_call_id from last_assistant_message: {tool_call_id}")
            
            if tool_call_id:
                msg_dict["tool_call_id"] = tool_call_id
                
            # function name 처리
            if hasattr(message, "name"):
                msg_dict["name"] = message.name
            elif last_assistant_message and "tool_calls" in last_assistant_message.get("additional_kwargs", {}):
                tool_call = last_assistant_message["additional_kwargs"]["tool_calls"][0]
                msg_dict["name"] = tool_call.get("function", {}).get("name", "tool")
                
            # 아티팩트가 있는 경우 처리
            if hasattr(message, "artifact") and message.artifact:
                msg_dict["metadata"] = {"artifacts": [message.artifact]}
        
        # AIMessage 추가 속성 처리
        if isinstance(message, AIMessage):
            additional_kwargs = getattr(message, "additional_kwargs", {})
            if additional_kwargs:
                msg_dict.update(additional_kwargs)
            last_assistant_message = msg_dict
            
        openai_messages.append(msg_dict)
    
    return openai_messages

def _get_role(message: BaseMessage) -> str:
    """메시지 타입에 따른 역할 반환"""
    if isinstance(message, HumanMessage):
        return "user"
    elif isinstance(message, AIMessage):
        return "assistant"
    elif isinstance(message, SystemMessage):
        return "system"
    elif isinstance(message, ToolMessage):
        return "tool"
    else:
        return "user"
