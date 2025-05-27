"""Background processing graph implementation."""
from typing import Dict, Any
from uuid import UUID
from langgraph.graph import Graph, END

from ..services.message_service import MessageService
from .nodes.processor import conversation_processor_node
from .nodes.analyzer import conversation_analyzer_node
from .nodes.summarizer import conversation_summarizer_node
from .state import BackgroundState, create_initial_state

import graphviz


def build_background_graph() -> Graph:
    """Build the background processing graph.
    
    This graph processes conversations through three stages:
    1. Processing: Normalize and validate messages
    2. Analysis: Analyze conversation content
    3. Summarization: Generate final summary
    
    Returns:
        Graph: Configured processing graph
    """
    workflow = Graph()
    
    # Add nodes
    workflow.add_node("processor", conversation_processor_node)
    workflow.add_node("analyzer", conversation_analyzer_node)
    workflow.add_node("summarizer", conversation_summarizer_node)
    
    # Set entry point
    workflow.set_entry_point("processor")
    
    # Define state-based routing
    def state_conditional(state: Dict[str, Any]) -> str:
        """Route to next node based on state.
        
        Args:
            state: Current processing state
            
        Returns:
            str: Next node or END
        """
        if state.get("error"):
            return END
            
        next_step = state.get("next_step", "end")
        return {
            "analyze": "analyzer",
            "summarize": "summarizer",
            "end": END
        }.get(next_step, END)
    
    # Add edges
    workflow.add_conditional_edges(
        source="processor",
        path=state_conditional,
        path_map={
            "analyzer": "analyzer",
            "summarizer": "summarizer",
            "end": END
        }
    )
    
    workflow.add_conditional_edges(
        source="analyzer",
        path=state_conditional,
        path_map={
            "summarizer": "summarizer",
            "end": END
        }
    )
    
    workflow.add_edge("summarizer", END)
    
    return workflow


async def process_session(session_id: UUID) -> BackgroundState:
    """Process a session's messages through the background graph.
    
    Args:
        session_id: UUID of the session to process
        
    Returns:
        BackgroundState: Final processing state
    """
    # Get messages
    messages = MessageService().get_session_messages(session_id)
    
    # Create initial state
    initial_state = create_initial_state(
        conversation_id=str(session_id),
        messages=messages,
        metadata={
            "session_id": str(session_id)
        }
    )
    
    # Run graph
    return await build_background_graph().ainvoke(initial_state)


def save_graph_visualization(graph: Graph, output_name: str = 'background_graph'):
    """Save a visualization of the background graph using graphviz.
    
    Args:
        graph: The graph to visualize
        output_name: Name for the output file (without extension)
    """
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
