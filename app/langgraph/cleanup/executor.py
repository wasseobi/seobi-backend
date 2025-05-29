"""Cleanup graph executor."""
from typing import Dict, List, Callable, Any
from datetime import datetime
import uuid

from .graph import build_graph

def create_cleanup_executor() -> Callable:
    """Create a cleanup graph executor."""

    # Build and compile graph
    workflow = build_graph()
    compiled_graph = workflow.compile()
    
    def invoke(
        session_id: uuid.UUID,
        conversation_history: List[Dict]
    ) -> Dict[str, Any]:
        """Execute the cleanup graph with session data."""
        
        # Initialize state
        state = {
            "session_id": str(session_id),
            "conversation_history": conversation_history,
            "analysis_result": None,
            "generated_tasks": None,
            "error": None,
            "start_time": datetime.now(),
            "end_time": None
        }
        
        try:
            # Execute graph
            result = compiled_graph.invoke(state)
            
            # Ensure we have a valid result
            if isinstance(result, dict):
                if result.get("error"):
                    print(f"Cleanup error for session {session_id}: {result['error']}")
                return result
            return state
            
        except Exception as e:
            import traceback
            traceback.print_exc()
            state["error"] = f"Failed to execute cleanup: {str(e)}"
            return state
    
    return invoke 