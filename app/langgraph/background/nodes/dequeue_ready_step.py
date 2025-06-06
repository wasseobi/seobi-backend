from app.langgraph.background.bg_state import BGState, PlanStep
from typing import Dict

def dequeue_ready_step(state: BGState) -> BGState:
    """
    ready_queue에서 다음 PlanStep 하나를 꺼냄
    - 없으면 finalize_task_result로 분기
    - 있으면 run_tool로 분기
    """
    task = state.get("task")
    if not task:
        return {
            **state,
            "error": "No task initialized",
            "finished": True
        }

    ready_queue = task.get("ready_queue", [])
    plan = task.get("plan", {})

    if not ready_queue:
        return {
            **state
        }

    step_id = ready_queue[0]
    step = plan.get(step_id)

    if not step:
        return {
            **state,
            "error": f"Step {step_id} not found in plan",
            "finished": True
        }

    step["status"] = "running"
    task["plan"][step_id] = step

    return {
        **state,
        "task": task,
        "step": step
    }