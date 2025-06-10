"""Graph module for General Agent implementation (MCP + 직접 구현 도구 통합)."""
from typing import Dict, List, Optional, Sequence, TypedDict, Union
from langgraph.graph import END, StateGraph
from langchain_core.messages import BaseMessage
import logging

from .nodes.model_node import model_node
from .nodes.summarize_node import summarize_node
from .nodes.cleanup_node import cleanup_node
from .nodes.tool_node import call_tool
from ..tools import agent_tools
from .agent_state import AgentState

# 로거 설정
log = logging.getLogger(__name__)


def build_graph():
    """Build the conversation flow graph (MCP + 직접 구현 도구 통합)."""
    # StateGraph 생성 시 초기 상태 설정
    workflow = StateGraph(dict)  # AgentState 대신 dict 사용

    # Create tool node function that accepts state
    def tool_node(state):
        return call_tool(state, agent_tools)

    # Add nodes
    workflow.add_node("agent", model_node)
    workflow.add_node("tool", tool_node)
    workflow.add_node("cleanup", cleanup_node)
    workflow.add_node("summarize", summarize_node)

    # Set entry point
    workflow.set_entry_point("agent")    # 조건 분기 함수
    def state_conditional(state: Union[AgentState, Dict]) -> str:
        try:
            if isinstance(state, AgentState):
                next_step = state.get("next_step")
            else:
                # state가 딕셔너리인 경우
                next_step = state.get("next_step") if isinstance(state, dict) else None
                
            print(f"🔀 State conditional - next_step: {next_step}")
            
            if next_step == "end":
                return "cleanup"
            elif next_step == "tool":
                return "tool"
            elif next_step == "cleanup":
                return "cleanup"
            else:
                # 기본값: 도구 사용 여부 확인
                messages = state.get("messages", []) if isinstance(state, dict) else getattr(state, "messages", [])
                if messages:
                    last_message = messages[-1]
                    # 마지막 메시지가 AI 응답이고 tool_calls가 없으면 종료
                    if (hasattr(last_message, "additional_kwargs") and 
                        "tool_calls" not in last_message.additional_kwargs):
                        return "cleanup"
                return "tool"  # 기본값
        except Exception as e:
            log.error(f"[Graph] Error in state_conditional: {str(e)}")
            return "cleanup"  # 오류 시 cleanup으로

    # Summarize는 cleanup에서 처리 후 상태에 따라 분기
    def after_cleanup(state: Union[AgentState, Dict]) -> str:
        try:
            if isinstance(state, AgentState):
                next_step = state.get("next_step")
            else:
                next_step = state.get("next_step") if isinstance(state, dict) else None
            
            return next_step or "end"
        except Exception as e:
            log.error(f"[Graph] Error in after_cleanup: {str(e)}")
            return "end"

    # 엣지 연결
    workflow.add_conditional_edges(
        "agent",
        state_conditional,
        {
            "tool": "tool",
            "cleanup": "cleanup",
        },
    )

    workflow.add_conditional_edges(
        "cleanup",
        after_cleanup,
        {
            "summarize": "summarize",
            "end": END,
        },
    )

    workflow.add_edge("tool", "agent")
    workflow.add_edge("summarize", END)

    return workflow


def mcp_graph(mcp_tools):
    """MCP Graph 생성 함수 (MCP + 직접 구현 도구 통합)"""
    print("🔧 MCP Tools:", mcp_tools)
    print("🔧 Direct Tools:", agent_tools)

    # 통합된 그래프 생성
    workflow = build_graph()
    
    # 그래프 컴파일
    app = workflow.compile()
    
    return app