"""Graph module for LangGraph implementation."""
from typing import Dict, List, Optional, Sequence, TypedDict, Union
from langgraph.graph import END, StateGraph
from langgraph.prebuilt import ToolNode
from langchain_core.messages import BaseMessage

from .nodes.model_node import model_node
from .nodes.summarize_node import summarize_node
from ..tools import agent_tools
from .agent_state import AgentState


def build_graph():
    """Build the conversation flow graph."""    # Create graph
    workflow = StateGraph(AgentState)

    # Create Runnable nodes
    tool_node = ToolNode(agent_tools, handle_tool_errors=True)    # Add nodes
    workflow.add_node("agent", model_node)
    workflow.add_node("tool", tool_node)
    workflow.add_node("summarize", summarize_node)

    # Set entry point
    workflow.set_entry_point("agent")

    # 조건 분기 함수
    def state_conditional(state: AgentState) -> str:
        return state.get("next_step", "end")

    def should_summarize(state: AgentState) -> bool:
        """Check if summarization is needed based on the number of messages."""
        messages = state.get("messages", [])
        if len(messages) > 5:
            return "summarize"
        return END

    workflow.add_conditional_edges("agent", state_conditional, {
        "summarize": "summarize",
        "model": "agent",
        "tool": "tool",
        "end": END
    })
    workflow.add_conditional_edges("summarize", should_summarize, {
        "end": END
    })
    workflow.add_edge("tool", "agent")

    return workflow
