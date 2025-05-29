"""Graph module for cleanup implementation."""
from langgraph.graph import Graph

from .nodes.analyze_conversation import AnalyzeConversationNode
from .nodes.generate_tasks import GenerateTasksNode
from .edges.cleanup_edges import should_continue, get_edge_map


def build_graph() -> Graph:
    """Build the cleanup graph."""
    
    # Create graph
    workflow = Graph()
    
    # Create nodes
    analyze_node = AnalyzeConversationNode()
    generate_node = GenerateTasksNode()
    
    # Add nodes
    workflow.add_node("analyze_conversation", analyze_node)
    workflow.add_node("generate_tasks", generate_node)
    
    # Set entry point
    workflow.set_entry_point("analyze_conversation")
    
    # Add conditional edges
    workflow.add_conditional_edges(
        source="analyze_conversation",
        path=should_continue,
        path_map=get_edge_map()
    )
    workflow.add_conditional_edges(
        source="generate_tasks",
        path=should_continue,
        path_map=get_edge_map()
    )
    
    return workflow 