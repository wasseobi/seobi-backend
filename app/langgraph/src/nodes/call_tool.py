"""외부 도구를 실행하는 모듈입니다."""
from typing import Dict, Any, List
from datetime import datetime
from langchain.schema import HumanMessage, AIMessage, SystemMessage, BaseMessage
from langchain_core.runnables import RunnableLambda
from src.state import ChatState
from src.tools import get_tools

def ensure_valid_messages(messages: List[BaseMessage]) -> List[BaseMessage]:
    """메시지 리스트가 유효한지 확인하고 필터링합니다."""
    if not messages:
        return []
    return [msg for msg in messages if isinstance(msg, (HumanMessage, AIMessage, SystemMessage))]

def call_tool(state: ChatState) -> Dict:
    """ToolNode 기반 도구 실행 래퍼."""
    try:
        intent = state["parsed_intent"]
        if not intent or "intent" not in intent:
            raise ValueError("의도 분석 결과가 없습니다.")
        tool_name = intent["intent"]
        tool_input = intent.get("params", {})

        # 도구 목록에서 해당 이름의 tool을 찾음
        tools = get_tools()
        tool = next((t for t in tools if t.name == tool_name), None)
        if not tool:
            raise ValueError(f"등록되지 않은 도구: {tool_name}")

        print(f"🛠️ ToolNode 실행: {tool_name}")
        print(f"📥 입력값: {tool_input}")

        # ToolNode 기반 실행
        tool_node = RunnableLambda(tool)
        result = tool_node.invoke(tool_input)
        if not isinstance(result, dict):
            result = {"result": result}
        print(f"📤 실행 결과: {result}")

        return {
            "executed_result": {
                "success": True,
                "action": tool_name,
                "details": result,
                "error": None
            },
            "messages": state.get("messages", [])
        }
    except Exception as e:
        print(f"❌ ToolNode 실행 중 오류 발생: {str(e)}")
        return {
            "executed_result": {
                "success": False,
                "action": state.get("parsed_intent", {}).get("intent", "unknown"),
                "details": {},
                "error": {"message": str(e)}
            },
            "messages": state.get("messages", [])
        }
