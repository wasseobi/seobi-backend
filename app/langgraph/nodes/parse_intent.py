"""사용자 입력의 의도를 분석하고, 필요한 경우 도구를 선택하는 모듈입니다."""
import os
import json
from typing import Dict, List, Any, Optional
from langchain.schema import HumanMessage, SystemMessage, AIMessage, BaseMessage
from app.utils.openai_client import get_completion, get_openai_client
from app.langgraph.tools import get_tools
from app.langgraph.state import ChatState

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

        # 시스템 프롬프트 개선
        system_prompt = """당신은 사용자의 의도를 파악하여 적절한 도구를 선택하는 AI입니다.
아래 규칙을 엄격하게 따라주세요.

사용 가능한 도구:

1. 시간 관련 질문 (예: "지금 몇 시야?", "현재 시각 알려줘")
   - Tool: get_current_time
   - 필수: 시간과 관련된 모든 질문에 사용
   - 형식: {"tool_calls":[{"type":"function","function":{"name":"get_current_time","arguments":"{}"}}]}

2. 검색 질문 (예: "대전역이 어디야?", "날씨 어때?")
   - Tool: google_search
   - 필수: 외부 정보가 필요한 모든 질문에 사용
   - 형식: {"tool_calls":[{"type":"function","function":{"name":"google_search","arguments":{"query":"검색어","num_results":3}}}]}

3. 일정 등록 (예: "내일 2시에 회의 잡아줘")
   - Tool: schedule_meeting
   - 필수: 일정 관련된 모든 요청에 사용
   - 형식: {"tool_calls":[{"type":"function","function":{"name":"schedule_meeting","arguments":{"datetime_str":"YYYY-MM-DDTHH:MM:SS","duration":"1h","title":"회의"}}}]}

엄격한 규칙:
1. 반드시 위 형식대로만 응답하세요
2. 시간 관련 질문에는 무조건 get_current_time을 선택하세요
3. 도구가 필요하지 않은 일반 대화는 그냥 텍스트로 응답하세요
4. JSON 응답시 들여쓰기를 지켜주세요
5. arguments는 항상 유효한 JSON 형식이어야 합니다"""

        messages = [
            {"role": "system", "content": system_prompt},
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
