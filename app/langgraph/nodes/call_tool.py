"""외부 도구를 실행하는 모듈입니다."""
from typing import Dict, Any, List
from datetime import datetime
from langchain.schema import HumanMessage, AIMessage, SystemMessage, BaseMessage
from app.langgraph.state import ChatState
from app.langgraph.tools import get_tools
from langchain_core.messages import AIMessage
from langgraph.prebuilt import ToolNode

def ensure_valid_messages(messages: List[BaseMessage]) -> List[BaseMessage]:
    """메시지 리스트가 유효한지 확인하고 필터링합니다."""
    if not messages:
        return []
    return [msg for msg in messages if isinstance(msg, (HumanMessage, AIMessage, SystemMessage))]

def call_tool(state: ChatState) -> Dict:
    """ToolNode 기반 도구 실행 래퍼 (AIMessage tool_calls 기반 병렬 도구 실행 지원)."""
    try:
        # state가 list나 dict로 들어올 수 있으므로 ChatState로 변환
        if isinstance(state, (list, dict)):
            state = ChatState.from_dict(state)

        # messages에서 마지막 AIMessage 추출 (tool_calls 기반)
        messages = state["messages"]
        last_msg = messages[-1] if messages else None
        # tool_calls가 있는 AIMessage가 아니면 일반 반환
        if not (isinstance(last_msg, AIMessage) and getattr(last_msg, "tool_calls", None)):
            return state.to_dict()

        # 도구 리스트 생성 및 ToolNode 초기화
        tools = get_tools()
        tool_node = ToolNode(tools, handle_tool_errors=True)

        # ToolNode의 invoke 사용 (AIMessage 포함 messages 리스트 전달)
        tool_result = tool_node.invoke({"messages": [last_msg]})

        # 결과 병합: 기존 state + 도구 실행 결과 메시지
        result = state.to_dict()
        # tool_result["messages"]는 ToolMessage 리스트
        result["messages"] = messages + tool_result.get("messages", [])
        result["executed_result"] = {
            "success": True,
            "details": tool_result.get("messages", []),
            "error": None
        }
        return result
    except Exception as e:
        result = state.to_dict()
        result["executed_result"] = {
            "success": False,
            "details": {},
            "error": {"message": str(e)}
        }
        return result
