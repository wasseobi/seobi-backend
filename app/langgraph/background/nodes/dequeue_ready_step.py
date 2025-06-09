from app.langgraph.background.bg_state import BGState, PlanStep
from app.utils.auto_task_utils import get_current_step_message
from app.services.auto_task_service import AutoTaskService
from typing import Dict

auto_task_service = AutoTaskService()

def dequeue_ready_step(state: BGState) -> BGState:
    """
    ready_queue에서 다음 PlanStep 하나를 꺼냄
    - 없으면 finalize_task_result로 분기
    - 있으면 run_tool로 분기
    """
    task = state.get("task")
    if not task:
        state["error"] = "No task initialized"
        state["finished"] = True
        state["step"] = None
        return state

    ready_queue = task.get("ready_queue", [])
    plan = task.get("plan", {})

    if not ready_queue:
        state["step"] = None
        return state

    step_id = ready_queue[0]
    step = plan.get(step_id)

    if not step:
        state["error"] = f"Step {step_id} not found in plan"
        state["finished"] = True
        state["step"] = None
        return state

    step["status"] = "running"
    task["plan"][step_id] = step

    # auto task current_step update + 디버그 메시지
    tool = step.get("tool")
    status = step.get("status")
    msg = get_current_step_message(tool, status)
    auto_task_id = str(task["task_id"])
    print(f"[DEBUG][dequeue_ready_step] current_step update: tool={tool}, status={status}, msg={msg}, auto_task_id={auto_task_id}")
    auto_task_service.update(auto_task_id, current_step=msg)

    state["step"] = step
    return state