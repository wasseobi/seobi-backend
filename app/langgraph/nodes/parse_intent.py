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
    # function calling JSON 파싱
    try:
        # JSON 추출 (응답에 일반 텍스트와 JSON이 섞여 있을 수 있으므로)
        json_match = re.search(r'\{\s*"tool_calls".*\}', response_content, re.DOTALL)
        if json_match:
            tool_json = json.loads(json_match.group(0))
            tool_calls = tool_json.get("tool_calls")
            if tool_calls and isinstance(tool_calls, list):
                tool = tool_calls[0]
                func = tool.get("function", {})
                tool_name = func.get("name")
                arguments = func.get("arguments")
                params = json.loads(arguments) if arguments else {}
                parsed_intent = {"intent": tool_name, "params": params}
    except Exception:
        pass

    return {
        "parsed_intent": parsed_intent,
        "messages": ensure_valid_messages(messages)
    }
