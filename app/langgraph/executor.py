"""Agent 실행기 생성."""
from typing import Dict, List, Callable, Any
from langchain_core.messages import BaseMessage, HumanMessage, AIMessage

from app.langgraph.graph import build_graph

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
            
        # 초기 상태 설정
        state = {
            "messages": chat_history + [HumanMessage(content=input_text)],
            "current_input": input_text,
            "scratchpad": [],
            "step_count": 0,  # 단계 카운터 초기화
            "next_step": "agent"  # 초기 상태를 agent로 설정
        }
        
        try:
            # invoke 메서드로 그래프 실행
            result = compiled_graph.invoke(state)
            print("\nGraph execution result:", result)  # 디버깅용
            
            if isinstance(result, dict) and "messages" in result:
                return result
            return state  # 기본 상태 반환
        except Exception as e:
            print(f"Graph execution error: {type(e)} - {str(e)}")
            import traceback
            traceback.print_exc()
            state["messages"].append(AIMessage(content="죄송합니다. 처리 중 오류가 발생했습니다."))
            return state
    
    return invoke
