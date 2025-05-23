"""외부 도구를 실행하는 모듈입니다."""
from typing import Dict, List
from langchain.schema import HumanMessage, SystemMessage, BaseMessage, FunctionMessage
from langchain_core.messages import AIMessage
from app.langgraph.state import ChatState
from app.langgraph.tools import get_tools

def ensure_valid_messages(messages: List[BaseMessage]) -> List[BaseMessage]:
    """메시지 리스트가 유효한지 확인하고 필터링합니다."""
    if not messages:
        return []
    return [msg for msg in messages if isinstance(msg, (HumanMessage, AIMessage, SystemMessage, FunctionMessage))]

def call_tool(state: ChatState) -> Dict:
    """ToolNode 기반 도구 실행 래퍼"""
    try:
        if isinstance(state, (list, dict)):
            state = ChatState.from_dict(state)

        messages = state["messages"]
        last_msg = messages[-1] if messages else None
        
        # tool_calls 파싱
        if isinstance(last_msg, HumanMessage):
            return state.to_dict()

        content = last_msg.content if last_msg else None
        if isinstance(content, str):
            try:
                import json
                content = json.loads(content)
            except json.JSONDecodeError as e:
                return state.to_dict()
                
        tool_calls = content.get("tool_calls", []) if isinstance(content, dict) else []
        
        if not tool_calls:
            return state.to_dict()
        
        # 도구 실행 준비
        tools = get_tools()
        tool_name = tool_calls[0]["function"]["name"]
        tool_args = tool_calls[0]["function"]["arguments"]
        
        if isinstance(tool_args, str):
            try:
                tool_args = json.loads(tool_args)
            except json.JSONDecodeError:
                tool_args = {}

        # 도구 실행
        tool_message = FunctionMessage(
            name=tool_name,
            content="",
            additional_kwargs={"name": tool_name, "arguments": tool_args}
        )
        
        result = None
        for tool in tools:
            if tool.name == tool_name:
                # invoke 메서드 사용
                result = tool.invoke(tool_args or "")
                break
        
        if result:
            tool_message.content = str(result)
            
        # 결과 병합
        result_dict = state.to_dict()
        result_dict["messages"] = messages + [tool_message]
        result_dict["executed_result"] = {
            "success": True,
            "details": result,
            "error": None
        }
        return result_dict
        
    except Exception as e:
        result = state.to_dict()
        result["executed_result"] = {
            "success": False,
            "details": {},
            "error": {"message": str(e)}
        }
        return result
