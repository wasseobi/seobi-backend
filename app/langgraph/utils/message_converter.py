"""메시지 변환 유틸리티."""
from typing import List, Dict, Any
from langchain_core.messages import BaseMessage, HumanMessage, AIMessage, SystemMessage, ToolMessage

def convert_to_openai_messages(messages: List[BaseMessage]) -> List[Dict[str, Any]]:
    """LangChain 메시지를 OpenAI 형식으로 변환.
    
    Args:
        messages: LangChain BaseMessage 객체 리스트
        
    Returns:
        OpenAI 메시지 형식의 딕셔너리 리스트
    """
    openai_messages = []
    last_assistant_message = None
    
    for message in messages:
        # 기본 메시지 구조
        msg_dict = {
            "content": message.content
        }
        
        # 역할 설정
        msg_dict["role"] = _get_role(message)
        
        # ToolMessage 특수 처리
        if isinstance(message, ToolMessage):
            # 이전 assistant 메시지가 있고 tool_calls가 있는지 확인
            if last_assistant_message and "tool_calls" in last_assistant_message.get("additional_kwargs", {}):
                tool_call = last_assistant_message["additional_kwargs"]["tool_calls"][0]
                msg_dict.update({
                    "tool_call_id": tool_call.get("id", message.tool_call_id),
                    "name": tool_call.get("function", {}).get("name", "tool")
                })
                
                # 아티팩트가 있는 경우 처리
                if hasattr(message, "artifact") and message.artifact:
                    msg_dict["metadata"] = {"artifacts": [message.artifact]}
            else:
                # tool 메시지를 assistant 메시지로 변환
                msg_dict["role"] = "assistant"
        
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
