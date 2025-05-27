"""Background processing executor."""
from typing import Dict, Any, Optional, Callable
from uuid import UUID
from flask import current_app
import graphviz
from langgraph.graph import Graph

from .graph import build_background_graph
from .state import BackgroundState, create_initial_state
from ..services.message_service import MessageService


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


def create_background_executor() -> Callable[[UUID], BackgroundState]:
    """백그라운드 처리 실행기를 생성합니다.
    
    Returns:
        Callable: 세션 처리를 위한 실행 함수
    """
    # 그래프 생성 및 컴파일
    graph = build_background_graph()
    
    # 그래프 시각화 저장 (개발 환경에서만)
    save_graph_visualization(graph, 'background_workflow')
    
    compiled_graph = graph.compile()
    
    async def execute_session(
        session_id: UUID,
        metadata: Optional[Dict[str, Any]] = None
    ) -> BackgroundState:
        """세션 메시지를 처리합니다.
        
        Args:
            session_id: 처리할 세션의 UUID
            metadata: 추가 메타데이터
            
        Returns:
            BackgroundState: 처리 결과 상태
        """
        try:
            # 메시지 조회
            messages = MessageService().get_session_messages(session_id)
            
            # 초기 상태 생성
            initial_state = create_initial_state(
                conversation_id=str(session_id),
                messages=messages,
                metadata={
                    "session_id": str(session_id),
                    **(metadata or {})
                }
            )
            
            # 그래프 실행
            result = await compiled_graph.ainvoke(initial_state)
            
            if isinstance(result, dict) and "error" not in result:
                return result
                
            current_app.logger.error(f"Graph execution failed: {result.get('error', 'Unknown error')}")
            return {
                **initial_state,
                "error": result.get("error", "Processing failed"),
                "next_step": "end"
            }
            
        except Exception as e:
            current_app.logger.error(f"Error in background executor: {str(e)}")
            return {
                "conversation_id": str(session_id),
                "error": str(e),
                "next_step": "end"
            }
    
    return execute_session


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