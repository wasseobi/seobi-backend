"""Graph module for LangGraph implementation."""
from typing import Dict
from langgraph.graph import Graph, END
from langgraph.prebuilt import ToolNode

from .nodes.model_node import model_node
from .nodes.summarize_node import summarize_node
from ..tools import agent_tools


def build_graph():
    """Build the conversation flow graph."""    # Create graph
    workflow = Graph()
    
    # Create Runnable nodes
    tool_node = ToolNode(agent_tools, handle_tool_errors=True)    # Add nodes
    workflow.add_node("agent", model_node)
    workflow.add_node("tool", tool_node)
    workflow.add_node("summarize", summarize_node)
    
    # Set entry point
    workflow.set_entry_point("agent")
    
    # Define condition function for edges
    def state_conditional(state: Dict) -> str:
        return state.get("next_step", "end")
    
    # Add conditional edges
    workflow.add_edge("agent", "summarize")
    workflow.add_edge("summarize", "tool")
    workflow.add_edge("tool", "agent")

        
    return workflow
