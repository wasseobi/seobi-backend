"""Graph module for LangGraph implementation."""
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
log = logging.getLogger("langgraph_debug")


def build_graph():
    """Build the conversation flow graph."""
    # 상태 초기화 함수 정의
    def init_state():
        log.info("[Graph] Initializing new state")
        state = AgentState()
        try:
            log.info(f"[Graph] Initialized state: {state.to_dict()}")
        except Exception as e:
            log.error(f"[Graph] Error in init_state: {str(e)}")
        return state

    # StateGraph 생성 시 초기 상태 설정
    workflow = StateGraph(dict, init_state)  # AgentState 대신 dict 사용

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
        log.info(f"[Graph] state_conditional - state type: {type(state)}")
        try:
            if isinstance(state, AgentState):
                next_step = state.get("next_step")
            else:
                # state가 딕셔너리인 경우
                log.info(f"[Graph] state keys: {state.keys() if hasattr(state, 'keys') else 'no keys method'}")
                next_step = state.get("next_step") if isinstance(state, dict) else None
                
            log.info(f"[Graph] state_conditional - next_step: {next_step}")
            if next_step == "end":
                return "cleanup"
            return next_step or "tool"
        except Exception as e:
            log.error(f"[Graph] Error in state_conditional: {str(e)}")
            return "tool"

    # Summarize는 cleanup에서 처리 후 상태에 따라 분기
    def after_cleanup(state: Union[AgentState, Dict]) -> str:
        log.info(f"[Graph] after_cleanup - state type: {type(state)}")
        try:
            if isinstance(state, AgentState):
                next_step = state.get("next_step")
            else:
                log.info(f"[Graph] state keys: {state.keys() if hasattr(state, 'keys') else 'no keys method'}")
                next_step = state.get("next_step") if isinstance(state, dict) else None
            
            log.info(f"[Graph] after_cleanup - next_step: {next_step}")
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
