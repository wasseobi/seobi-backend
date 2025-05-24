"""메시지 변환 유틸리티."""
from typing import Dict, List
from langchain_core.messages import BaseMessage, FunctionMessage

def convert_to_openai_messages(messages: List[BaseMessage]) -> List[Dict]:
    """메시지를 OpenAI 형식으로 변환."""
    print("\n[디버그] OpenAI 메시지 변환 시작")
    print(f"변환할 메시지 수: {len(messages)}")
    converted = []
    
    # 시스템 메시지는 한 번만 추가
    system_added = False
    
    for i, msg in enumerate(messages):
        if msg.type == "system" and not system_added:
            converted.append({
                "role": "system",
                "content": msg.content
            })
            system_added = True
            
        elif msg.type == "human":
            converted.append({
                "role": "user",
                "content": msg.content
            })
            
        elif msg.type == "ai":
            msg_dict = {
                "role": "assistant",
                "content": msg.content
            }
            if hasattr(msg, "additional_kwargs") and "tool_calls" in msg.additional_kwargs:
                msg_dict["tool_calls"] = msg.additional_kwargs["tool_calls"]
            converted.append(msg_dict)
            
        elif isinstance(msg, FunctionMessage) or getattr(msg, "type", "") == "tool":
            if i > 0 and hasattr(messages[i-1], "additional_kwargs") and "tool_calls" in messages[i-1].additional_kwargs:
                tool_result = {
                    "role": "tool",
                    "content": str(msg.content),
                    "tool_call_id": getattr(msg, "tool_call_id", "") or msg.additional_kwargs.get("tool_call_id", ""),
                    "name": getattr(msg, "name", "") or msg.additional_kwargs.get("name", "search_web")
                }
                converted.append(tool_result)
            else:
                # tool_calls가 없는 경우, 검색 결과를 system 메시지로 추가
                converted.append({
                    "role": "system",
                    "content": f"다음 검색 결과를 참고하여 응답해주세요:\n{str(msg.content)}"
                })
    
    print(f"[디버그] 변환된 메시지:")
    for i, msg in enumerate(converted):
        print(f"- {i}번째 메시지:")
        print(f"  역할: {msg['role']}")
        print(f"  내용: {msg['content'][:100]}...")
        if "tool_calls" in msg:
            print(f"  도구 호출: {msg['tool_calls']}")
    
    return converted
