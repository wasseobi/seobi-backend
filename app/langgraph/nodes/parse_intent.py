"""사용자 입력의 의도를 분석하고, 필요한 경우 도구를 선택하는 모듈입니다."""
import os
import json
from typing import Dict, List, Any, Optional
from langchain.schema import HumanMessage, SystemMessage, AIMessage, BaseMessage
from app.utils.openai_client import get_completion, get_openai_client
from app.langgraph.tools import get_tools
from app.langgraph.state import ChatState
from app.langgraph.prompts.parse_intent_prompt import SYSTEM_PROMPT

def ensure_valid_messages(messages: List[BaseMessage]) -> List[BaseMessage]:
    if not messages:
        return []
    return [msg for msg in messages if isinstance(msg, (SystemMessage, HumanMessage, AIMessage)) and msg.content]

def parse_tool_response(response_content: str) -> Optional[dict]:
    """도구 선택 응답을 파싱합니다."""
    if not response_content.strip().startswith("{"):
        return None
        
    try:
        response = json.loads(response_content)
        tool_calls = response.get("tool_calls", [])
        
        if not tool_calls:
            return None
            
        tool_call = tool_calls[0]
        function = tool_call.get("function", {})
        
        if not function or "name" not in function:
            return None
            
        name = function["name"]
        arguments = function.get("arguments", "{}")
        print(f"[DEBUG][parse_intent] 도구 선택됨: {name}")
        
        return {
            "intent": name,
            "params": json.loads(arguments) if arguments else {}
        }
    except (json.JSONDecodeError, KeyError) as e:
        print(f"[DEBUG][parse_intent] 응답 파싱 실패: {str(e)}")
        return None

def parse_intent(state: Dict) -> Dict:
    """사용자 입력의 의도를 분석하고, 필요한 경우 도구를 선택합니다."""
    try:
        if isinstance(state, (list, dict)):
            state = ChatState.from_dict(state)

        user_input = state.get("user_input", "")
        if not user_input.strip():
            return {
                "parsed_intent": {"intent": "general_chat", "params": {}},
                "messages": []
            }

        messages = [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user_input}
        ]

        client = get_openai_client()
        response_content = get_completion(client, messages)

        print(f"[DEBUG][parse_intent] 모델 응답: {response_content}")

        if not response_content:
            raise ValueError("Empty response from model")

        # 모델 응답을 state에 추가할 메시지 생성
        ai_message = AIMessage(content=response_content)
        updated_messages = state.get("messages", []) + [ai_message]

        # 도구 선택 응답 파싱
        try:
            response = json.loads(response_content)
            if "tool_calls" in response and response["tool_calls"]:
                tool_call = response["tool_calls"][0]
                if "function" in tool_call:
                    function = tool_call["function"]
                    name = function["name"]
                    arguments = function.get("arguments", "{}")
                    print(f"[DEBUG][parse_intent] 도구 선택됨: {name}, 인자: {arguments}")
                    
                    parsed_intent = {
                        "intent": name,
                        "params": json.loads(arguments) if arguments else {}
                    }
                    
                    result = {
                        "parsed_intent": parsed_intent,
                        "messages": updated_messages
                    }
                    print(f"[DEBUG][parse_intent] 반환할 결과: {result}")
                    return result

        except json.JSONDecodeError as e:
            print(f"[parse_intent] JSON 파싱 실패: {str(e)}")

        # 일반 대화로 처리
        print("[DEBUG][parse_intent] 일반 대화로 처리")
        return {
            "parsed_intent": {"intent": "general_chat", "params": {}},
            "messages": updated_messages
        }

    except Exception as e:
        print(f"[parse_intent] Error: {str(e)}")
        return {
            "parsed_intent": {"intent": "general_chat", "params": {}},
            "messages": state.get("messages", [])
        }
