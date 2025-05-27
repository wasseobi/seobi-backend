"""Background processing graph implementation."""
from typing import Dict, Any
from uuid import UUID
from langgraph.graph import Graph, END

from .nodes.processor import conversation_processor_node
from .nodes.analyzer import conversation_analyzer_node
from .nodes.summarizer import conversation_summarizer_node
from .state import BackgroundState
from .executor import create_background_executor


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


# Create executor instance
_executor = create_background_executor()


async def process_session(session_id: UUID) -> BackgroundState:
    """Process a session's messages through the background graph.
    
    Args:
        session_id: UUID of the session to process
        
    Returns:
        BackgroundState: Final processing state
    """
    return await _executor(session_id)
