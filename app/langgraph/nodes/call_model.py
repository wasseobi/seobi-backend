import os
from typing import Dict, List
from langchain.schema import AIMessage, HumanMessage
from app.utils.openai_client import get_completion, get_openai_client
from langchain_openai import ChatOpenAI
from app.langgraph.tools import get_tools
from app.langgraph.state import ChatState
from app.langgraph.agent import model_with_tools

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
    # state가 list나 dict로 들어올 수 있으므로 ChatState로 변환
    if isinstance(state, (list, dict)):
        state = ChatState.from_dict(state)
    messages = state["messages"]
    # LangGraph agentic 구조: LLM이 tool_calls를 생성할 수 있도록 바인딩된 모델 사용
    response = model_with_tools.invoke(messages)
    return {
        "messages": messages + [response],
        "reply": getattr(response, "content", ""),
        "action_required": bool(getattr(response, "tool_calls", None)),
        "executed_result": {"tool_calls": getattr(response, "tool_calls", [])} if getattr(response, "tool_calls", None) else {}
    }
