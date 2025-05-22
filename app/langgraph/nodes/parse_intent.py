"""사용자 입력의 의도를 분석하고, 필요한 경우 ToolNode 기반의 tool intent를 반환하는 모듈입니다."""
import os
from typing import Dict, List, Any
from langchain.schema import HumanMessage, SystemMessage, AIMessage, BaseMessage
from app.utils.openai_client import get_completion, get_openai_client
from app.langgraph.tools import get_tools
from app.langgraph.state import ChatState

def ensure_valid_messages(messages: List[BaseMessage]) -> List[BaseMessage]:
    if not messages:
        return []
    return [msg for msg in messages if isinstance(msg, (SystemMessage, HumanMessage, AIMessage)) and msg.content]

def parse_intent(state: Dict) -> Dict:
    # state가 list나 dict로 들어올 수 있으므로 ChatState로 변환
    if isinstance(state, (list, dict)):
        state = ChatState.from_dict(state)

    user_input = state.get("user_input", "")
    if not user_input.strip():
        return {
            "parsed_intent": {"intent": "general_chat", "params": {}},
            "messages": []
        }

    tools = get_tools()
    prev_messages = state.get("messages", [])
    if prev_messages:
        messages = prev_messages + [HumanMessage(content=user_input)]
    else:
        messages = [HumanMessage(content=user_input)]

    # OpenAI function calling 포맷을 유도하는 시스템 프롬프트
    system_prompt = (
        "당신은 LangGraph 기반 AI입니다. 사용자의 요청이 도구(툴) 호출이 필요하면 반드시 아래 JSON 형식으로 응답하세요.\n"
        "예시: {\n  \"tool_calls\": [ { \"id\": \"tool-call-id\", \"type\": \"function\", \"function\": { \"name\": \"google_search\", \"arguments\": \"{\\\\\"query\\\\\": \\\\\"대전역 위치\\\\\"}\" } } ] }\n"
        "단순 대화라면 일반 답변만 하세요."
    )
    messages = [SystemMessage(content=system_prompt)] + messages

    client = get_openai_client()
    response_content = get_completion(
        client,
        messages=[{"role": "user", "content": msg.content} for msg in messages],
        max_completion_tokens=512
    )

    import json, re
    parsed_intent = {"intent": "general_chat", "params": {}}
    
    # 응답에서 tool_calls 추출 시도
    try:
        if response_content:
            response_json = json.loads(response_content)
            if "tool_calls" in response_json and response_json["tool_calls"]:
                tool_call = response_json["tool_calls"][0]
                if "function" in tool_call:
                    function = tool_call["function"]
                    parsed_intent["intent"] = function["name"]
                    if "arguments" in function:
                        try:
                            args = json.loads(function["arguments"])
                            parsed_intent["params"] = args
                        except json.JSONDecodeError:
                            print(f"[parse_intent] arguments 파싱 실패: {function['arguments']}")
    except json.JSONDecodeError:
        print(f"[parse_intent] response_content 파싱 실패: {response_content}")
    except Exception as e:
        print(f"[parse_intent] 예외 발생: {str(e)}")

    result = state.to_dict()
    result["parsed_intent"] = parsed_intent
    result["messages"] = messages
    return result
