from typing import Dict, Any, Callable
from .bg_state import BGState
from .graph import build_background_graph
import uuid

def create_background_executor() -> Callable:
    graph = build_background_graph()
    compiled_graph = graph.compile()

    def invoke(user_id: uuid.UUID) -> Dict[str, Any]:

        state = BGState(
            user_id=user_id,
            task=None,
            all_task_done=None,
            error=None,
            finished=False,
            step=None
        )

        try:
            result = compiled_graph.invoke(state)
            if isinstance(result, dict):
                return result
            return result
        
        except Exception as e:
            import traceback
            traceback.print_exc()
            state["error"] = str(e)
            state["finished"] = True
            return state
        
    return invoke
