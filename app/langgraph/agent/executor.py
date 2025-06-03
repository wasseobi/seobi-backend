"""Agent 실행기 생성."""
from typing import Dict, List, Callable, Any
from langchain_core.messages import BaseMessage, HumanMessage, AIMessage
from .agent_state import AgentState

from .graph import build_graph

def create_agent_executor() -> Callable:
    """Agent 실행기를 생성합니다."""
    graph = build_graph()
    compiled_graph = graph.compile()
    
    def invoke(
        input_text: str,
        chat_history: List[BaseMessage] = None
    ) -> Dict[str, Any]:
        """입력된 텍스트로 그래프를 실행합니다."""
        if chat_history is None:
            chat_history = []
            
        # 초기 상태 설정 (사용자 입력을 한 번만 추가)
        state = AgentState(
            messages=[],  # 빈 리스트로 시작
            current_input=input_text,  # 현재 입력만 저장
            scratchpad=[],
            step_count=0,
            next_step="agent"
        )
        
        try:
            # 그래프 실행
            result = compiled_graph.invoke(state)
            
            if isinstance(result, dict) and "messages" in result:
                return result
            return state
            
        except Exception as e:
            import traceback
            traceback.print_exc()
            state["messages"] = [AIMessage(content="죄송합니다. 처리 중 오류가 발생했습니다.")]
            return state
    
    return invoke
