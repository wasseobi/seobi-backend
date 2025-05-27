"""Background processing graph implementation."""
import graphviz

from typing import Dict, Any
from langgraph.graph import Graph, END

from .nodes.processor import conversation_processor_node
from .nodes.analyzer import conversation_analyzer_node
from .nodes.summarizer import conversation_summarizer_node


def build_background_graph():
    """Build the background processing graph.
    
    This graph processes conversations after they are completed, performing
    analysis, summarization, and other background tasks.
    """
    workflow = Graph()
    
    # Add processing nodes
    workflow.add_node("processor", conversation_processor_node)
    workflow.add_node("analyzer", conversation_analyzer_node)
    workflow.add_node("summarizer", conversation_summarizer_node)
    
    # Set entry point
    workflow.set_entry_point("processor")
    
    # Define condition function for edges
    def state_conditional(state: Dict[str, Any]) -> str:
        """Determine the next node based on the current state.
        
        Args:
            state: Current state dictionary containing processing results
            
        Returns:
            str: Next node to execute or END
        """
        # Check if there was an error
        if state.get("error"):
            return END
            
        # Get the next step from state
        next_step = state.get("next_step", "end")
        
        # Map next_step to actual node names
        if next_step == "analyze":
            return "analyzer"
        elif next_step == "summarize":
            return "summarizer"
        else:
            return END
    
    # Add conditional edges
    workflow.add_conditional_edges(
        source="processor",
        path=state_conditional,
        path_map={
            "analyzer": "analyzer",
            "summarizer": "summarizer",
            "end": END
        }
    )
    
    # Add edges from analyzer
    workflow.add_conditional_edges(
        source="analyzer",
        path=state_conditional,
        path_map={
            "summarizer": "summarizer",
            "end": END
        }
    )
    
    # Add edge from summarizer to end
    workflow.add_edge("summarizer", END)
    
    return workflow


def save_graph_visualization(graph: Graph, output_name: str = 'background_graph'):
    """Save a visualization of the background graph using graphviz."""
    
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