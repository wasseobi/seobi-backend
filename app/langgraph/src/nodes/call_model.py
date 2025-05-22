import os
from typing import Dict, List
from langchain.schema import AIMessage, HumanMessage
# Gemini용
from langchain.chat_models import init_chat_model
# Azure OpenAI(gpt-4o 등)용 (나중에 주석 해제)
from langchain.chat_models import AzureChatOpenAI

from src.tools import tools
from src.state import ChatState

# ===== Gemini용 LLM 초기화 =====
model = init_chat_model(
    os.getenv("DEFAULT_MODEL"),
    temperature=1.0,
    max_tokens=1024,
)
model_with_tools = model.bind_tools(tools)

# ===== Azure OpenAI(gpt-4o 등)용 LLM 초기화 (나중에 사용) =====
# model = AzureChatOpenAI(
#     deployment_name=os.getenv("AZURE_OPENAI_DEPLOYMENT_NAME", "o4-mini"),
#     temperature=1.0,
#     max_tokens=1024,
# )
# model_with_tools = model.bind_tools(tools)

def filter_empty_messages(messages: List) -> List:
    """빈 내용의 메시지를 필터링합니다."""
    return [msg for msg in messages if (
        isinstance(msg, (HumanMessage, AIMessage)) and 
        msg.content and 
        msg.content.strip()
    )]

def format_response(response: AIMessage) -> Dict:
    # ===== Gemini: 구조적 tool call이 오지 않으면 텍스트 패턴도 허용 (나중에 4o에서는 주석처리) =====
    action_required = (
        hasattr(response, "additional_kwargs") and bool(response.additional_kwargs.get("tool_calls"))
    )
    # Gemini에서만 사용: 텍스트에 tool 패턴이 있으면 action_required True
    # (4o로 전환 시 아래 if문 전체를 주석처리)
    content_to_check = response.content or ""
    # system_reply도 감지
    if hasattr(response, "system_reply") and response.system_reply:
        content_to_check += str(response.system_reply)
    if not action_required and content_to_check:
        if (
            "tool_code" in content_to_check
            or "google_search.run" in content_to_check
            or "current_time" in content_to_check
            or "schedule_meeting" in content_to_check
        ):
            action_required = True
    executed_result = {}
    if action_required and hasattr(response, "additional_kwargs"):
        executed_result = {"tool_calls": response.additional_kwargs.get("tool_calls")}
    return {
        "messages": [response],
        "reply": response.content if response.content else "",
        "action_required": action_required,
        "executed_result": executed_result
    }

def call_model(state: ChatState):
    messages = state["messages"]
    filtered_messages = filter_empty_messages(messages)
    if not filtered_messages:
        return {
            "messages": messages,
            "reply": "메시지가 비어있습니다.",
            "action_required": False,
            "executed_result": {}
        }
    try:
        response = model_with_tools.invoke(filtered_messages)
        print('🤖 모델 응답:')
        print(response)
        print()
        return format_response(response)
    except Exception as e:
        print(f"모델 호출 중 오류 발생: {str(e)}")
        return {
            "messages": messages,
            "reply": f"모델 호출 중 오류가 발생했습니다: {str(e)}",
            "action_required": False,
            "executed_result": {"error": str(e)}
        }
