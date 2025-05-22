import os
from typing import Dict, List
from langchain.schema import AIMessage, HumanMessage
from app.utils.openai_client import get_completion, get_openai_client
from app.langgraph.tools import tools
from app.langgraph.state import ChatState

def filter_empty_messages(messages: List) -> List:
    """빈 내용의 메시지를 필터링합니다."""
    return [msg for msg in messages if (
        isinstance(msg, (HumanMessage, AIMessage)) and 
        msg.content and 
        msg.content.strip()
    )]

def format_response(response: AIMessage) -> Dict:
    # ===== Azure OpenAI: tool_calls 기반 분기 =====
    action_required = (
        hasattr(response, "additional_kwargs") and bool(response.additional_kwargs.get("tool_calls"))
    )
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
        # 함수 내부에서만 클라이언트 생성
        client = get_openai_client()
        response_content = get_completion(
            client,
            messages=[{"role": "user", "content": msg.content} for msg in filtered_messages],
            max_completion_tokens=1024
        )
        print('🤖 모델 응답:')
        print(response_content)
        print()
        return {
            "messages": messages + [AIMessage(content=response_content)],
            "reply": response_content,
            "action_required": False,  # tool call 분기 필요시 추가 구현
            "executed_result": {}
        }
    except Exception as e:
        print(f"모델 호출 중 오류 발생: {str(e)}")
        return {
            "messages": messages,
            "reply": f"모델 호출 중 오류가 발생했습니다: {str(e)}",
            "action_required": False,
            "executed_result": {"error": str(e)}
        }
