"""Graph module for LangGraph implementation."""
from typing import Dict
from langgraph.graph import Graph
from langgraph.prebuilt import ToolNode

from .nodes.model_node import model_node
from .nodes.end_node import end_node
from .tools import search_web_tool, calculator_tool

def build_graph():
    """Build the conversation flow graph."""
    # Tools list
    tools = [search_web_tool, calculator_tool]
    
    # Create graph
    workflow = Graph()
    
    # Create Runnable nodes
    tool_node = ToolNode(tools, handle_tool_errors=True)
    
    # Add nodes
    workflow.add_node("agent", model_node)
    workflow.add_node("tool", tool_node)
    workflow.add_node("end", end_node)
    
    # Set entry point
    workflow.set_entry_point("agent")
    
    # Define condition function for edges
    def state_conditional(state: Dict) -> str:
        next_step = state.get("next_step", "end")
        print(f"\nNext step in state_conditional: {next_step}")  # 디버깅용
        return next_step
    
    # Add conditional edges
    workflow.add_conditional_edges(
        source="agent",
        path=state_conditional,
        path_map={"tool": "tool", "model": "agent", "end": "end"}
    )
    workflow.add_edge("tool", "agent")
    workflow.set_finish_point("end")
    
    return workflow
