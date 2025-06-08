"""Edge definitions for cleanup graph."""
from typing import Dict
from langgraph.graph import END

def should_continue(state: Dict) -> str:
    """Determine the next step in the cleanup graph."""
    if state.get("error"):
        return "end"
    if not state.get("analysis_result"):
        return "analyze_conversation"
    if not state.get("generated_tasks") is None:  # None이 아닌 경우 (빈 배열 포함)
        return "end"
    return "generate_tasks"

def get_edge_map() -> Dict[str, str]:
    """Get the mapping of edge conditions to target nodes."""
    return {
        "analyze_conversation": "analyze_conversation",
        "generate_tasks": "generate_tasks",
        "end": END
    } 