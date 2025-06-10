"""도구 호출 노드 (MCP + 직접 구현 도구 통합)."""
import json
from typing import List, Dict, Set, Union
from langchain_core.messages import BaseMessage, FunctionMessage, AIMessage
from langchain_core.tools import BaseTool
from app.langgraph.general_agent.agent_state import AgentState

import logging
log = logging.getLogger("langgraph_debug")

# 도구별 인자 매핑 정의
TOOL_ARG_MAPPING: Dict[str, Dict[str, str]] = {
    "search_web": {"__arg1": "query"},
    "calculator": {"__arg1": "expression"}
}

def _map_tool_arguments(function_name: str, arguments: Dict) -> Dict:
    """도구별 인자를 매핑하는 헬퍼 함수"""
    if "__arg1" not in arguments:
        return arguments
        
    if function_name in TOOL_ARG_MAPPING:
        arg_value = arguments["__arg1"]
        mapped_arg = TOOL_ARG_MAPPING[function_name]["__arg1"]
        return {mapped_arg: arg_value}
    
    return arguments

def _validate_tool_responses(messages: List[BaseMessage]) -> Set[str]:
    """도구 호출과 응답의 일관성을 검증하고 누락된 응답의 tool_call_id를 반환합니다."""
    missing_responses = set()
    tool_calls_map = {}  # tool_call_id -> function_name mapping
    response_ids = set()  # received response ids

    # 도구 호출 ID 수집
    for msg in messages:
        if hasattr(msg, "additional_kwargs"):
            # 도구 호출 확인
            if "tool_calls" in msg.additional_kwargs:
                for tool_call in msg.additional_kwargs["tool_calls"]:
                    if "id" in tool_call:
                        tool_calls_map[tool_call["id"]] = tool_call.get("function", {}).get("name")
            
            # 도구 응답 확인
            if isinstance(msg, FunctionMessage) and "tool_call_id" in msg.additional_kwargs:
                response_ids.add(msg.additional_kwargs["tool_call_id"])

    # 누락된 응답 확인
    for call_id, function_name in tool_calls_map.items():
        if call_id not in response_ids:
            missing_responses.add(call_id)
            log.error(f"[ToolNode] Missing response for tool call {call_id} (function: {function_name})")

    return missing_responses

def call_tool(state: Union[Dict, AgentState], tools: List[BaseTool] = None) -> Union[Dict, AgentState]:
    """도구를 호출하고 결과를 처리하는 노드 (MCP + 직접 구현 도구 통합)."""
    
    try:
        # state 타입 확인
        is_dict = isinstance(state, dict)
        
        # 마지막 AI 메시지에서 도구 호출 정보 추출
        messages = state.get("messages") if is_dict else state.messages
        if not messages:
            log.error("[ToolNode] No messages in state")
            log.error(f"[ToolNode] State keys: {state.keys() if is_dict else 'AgentState'}")
            # 기본 응답으로 처리
            if is_dict:
                state["next_step"] = "agent"
            else:
                state.next_step = "agent"
            return state
            
        last_message = messages[-1]
        
        # tool_calls 정보 추출 및 검증
        tool_calls = []
        if hasattr(last_message, "additional_kwargs"):
            tool_calls = last_message.additional_kwargs.get("tool_calls", [])
            
        if not tool_calls:
            if is_dict:
                state["next_step"] = "agent"
            else:
                state.next_step = "agent"
            return state
            
        # 모든 도구 목록 가져오기
        if tools is None:
            if is_dict:
                all_tools = []
                if state.get("mcp_tools"):
                    all_tools.extend(state["mcp_tools"])
                if state.get("direct_tools"):
                    all_tools.extend(state["direct_tools"])
                if not all_tools:
                    from ...tools import agent_tools
                    all_tools = agent_tools
            else:
                all_tools = state.get_all_tools()
                if not all_tools:
                    from ...tools import agent_tools
                    all_tools = agent_tools
        else:
            all_tools = tools
            
        # 각 tool call 처리
        for tool_call in tool_calls:
            try:
                if not isinstance(tool_call, dict) or "function" not in tool_call:
                    log.warning("[ToolNode] Invalid tool call format")
                    continue
                    
                # 도구 호출 정보 추출
                call_id = tool_call.get("id", "")
                function_info = tool_call["function"]
                function_name = function_info.get("name")
                
                # 인자 파싱
                arguments_str = function_info.get("arguments", "{}")
                try:
                    arguments = json.loads(arguments_str)
                    arguments = _map_tool_arguments(function_name, arguments)
                except json.JSONDecodeError:
                    arguments = {}

                # 도구 실행 (MCP 또는 직접 구현 도구)
                tool = next((t for t in all_tools if t.name == function_name), None)
                if tool:
                    result = tool.invoke(arguments)
                    
                    # 도구 실행 결과를 state에 저장
                    if is_dict:
                        state["tool_results"] = result
                        state["current_tool_call_id"] = call_id
                        state["current_tool_name"] = function_name
                    else:
                        state.set_tool_results(result)
                        state.current_tool_call_id = call_id
                        state.current_tool_name = function_name
                    
                else:
                    log.warning(f"[ToolNode] Tool '{function_name}' not found in available tools")
                    error_result = f"Tool '{function_name}' not found"
                    if is_dict:
                        state["tool_results"] = error_result
                        state["current_tool_call_id"] = call_id
                        state["current_tool_name"] = function_name
                    else:
                        state.set_tool_results(error_result)
                        state.current_tool_call_id = call_id
                        state.current_tool_name = function_name
                    
            except Exception as e:
                log.error(f"[ToolNode] Error processing tool call {function_name}: {str(e)}")
                # 오류 메시지를 tool 결과로 설정
                error_result = f"Error executing {function_name}: {str(e)}"
                if is_dict:
                    state["tool_results"] = error_result
                    state["current_tool_call_id"] = call_id
                    state["current_tool_name"] = function_name
                else:
                    state.set_tool_results(error_result)
                    state.current_tool_call_id = call_id
                    state.current_tool_name = function_name

        # 다음 단계를 agent로 설정하여 결과 처리
        if is_dict:
            state["next_step"] = "agent"
        else:
            state.next_step = "agent"
        print(f"🔄 Tool execution completed - moving to agent")
        return state
        
    except Exception as e:
        log.error(f"[ToolNode] Error in call_tool: {str(e)}", exc_info=True)
        if is_dict:
            state["error"] = str(e)
            state["next_step"] = "model"
        else:
            state.error = str(e)
            state.next_step = "model"
        return state 