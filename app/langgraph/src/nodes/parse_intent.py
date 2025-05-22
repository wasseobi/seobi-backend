"""사용자 입력의 의도를 분석하고, 필요한 경우 ToolNode 기반의 tool intent를 반환하는 모듈입니다."""
import os
from typing import Dict, List, Any
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain.schema import HumanMessage, SystemMessage, AIMessage, BaseMessage
from src.tools import get_tools
from src.state import ChatState

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
    model_name = os.getenv("DEFAULT_MODEL", "google_genai:gemini-2.0-flash")
    # Google Gemini 모델 사용
    model = ChatGoogleGenerativeAI(
        model=model_name.split(":", 1)[-1],
        temperature=0.1,
        max_tokens=512,
        google_api_key=os.getenv("GOOGLE_API_KEY")
    )
    model = model.bind_tools(tools)

    prev_messages = state.get("messages", [])
    if prev_messages:
        messages = prev_messages + [HumanMessage(content=user_input)]
    else:
        messages = [HumanMessage(content=user_input)]

    # 시스템 프롬프트는 첫 메시지로만 추가
    messages = [SystemMessage(content="사용자 입력에 따라 필요한 도구를 호출하세요. 도구가 필요하면 tool call을, 아니면 일반 답변을 하세요.")] + messages

    response = model.invoke(messages)

    parsed_intent = {}
    if hasattr(response, "tool_calls") and response.tool_calls:
        tool_call = response.tool_calls[0]
        parsed_intent = {
            "intent": tool_call["name"] if isinstance(tool_call, dict) and "name" in tool_call else tool_call.name,
            "params": tool_call.get("args", {}) if isinstance(tool_call, dict) else getattr(tool_call, "args", {})
        }
    else:
        parsed_intent = {
            "intent": "general_chat",
            "params": {}
        }

    return {
        "parsed_intent": parsed_intent,
        "messages": ensure_valid_messages(messages)
    }
