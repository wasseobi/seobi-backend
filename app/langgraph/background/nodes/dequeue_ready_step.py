from app.langgraph.background.bg_state import BGState, PlanStep
from app.utils.auto_task_utils import get_current_step_message

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

    # BGState(current_step)에만 append + 디버그 메시지
    tool = step.get("tool")
    status = step.get("status")
    msg = get_current_step_message(tool, status)
    history = state.get("current_step", [])
    history.append(msg)
    state["current_step"] = history
    print(f"[DEBUG][dequeue_ready_step] current_step update: history={history}")

    state["step"] = step
    return state