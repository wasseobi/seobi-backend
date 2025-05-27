"""Graph module for LangGraph implementation."""
from typing import Dict
from langgraph.graph import Graph, END
from langgraph.prebuilt import ToolNode

from .nodes.model_node import model_node
from ..tools import agent_tools


def build_graph():
    """Build the conversation flow graph."""    # Create graph
    workflow = Graph()
    
    # Create Runnable nodes
    tool_node = ToolNode(agent_tools, handle_tool_errors=True)    # Add nodes
    workflow.add_node("agent", model_node)
    workflow.add_node("tool", tool_node)
    
    # Set entry point
    workflow.set_entry_point("agent")
    
    # Define condition function for edges
    def state_conditional(state: Dict) -> str:
        return state.get("next_step", "end")
    
    # Add conditional edges
    workflow.add_conditional_edges(
        source="agent",
        path=state_conditional,
        path_map={"tool": "tool", "model": "agent", "end": END}
    )
    workflow.add_edge("tool", "agent")

        
    return workflow


def save_graph_visualization(graph: Graph, output_name: str = 'chatbot_graph'):
    """Save a visualization of the graph using graphviz.
    
    Args:
        graph: The LangGraph Graph object to visualize
        output_name: Name of the output file (without extension)
    """
    try:
        import graphviz
        # Create a new Digraph
        dot = graphviz.Digraph()
        dot.attr(rankdir='LR')
        
        # Add nodes from the graph's nodes
        for node in graph.nodes:
            dot.node(str(node), str(node))
            
        # Add edges from the graph's edges
        for edge in graph.edges:
            dot.edge(str(edge[0]), str(edge[1]))
            
        # Save the visualization
        dot.render(output_name, format='png', cleanup=True)
        print(f"\nGraph visualization saved as '{output_name}.png'")
    except Exception as e:
        print(f"\nCould not generate graph visualization: {e}")
        print("To enable graph visualization, install graphviz:")
        print("  pip install graphviz")
        print("  sudo apt-get install graphviz")
