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
    print(f"[DEBUG][dequeue_ready_step] ready_queue[0] step_id: {step_id}")
    step = plan.get(step_id)
    print(f"[DEBUG][dequeue_ready_step] plan.get(step_id): {step}")

    if not step:
        print(f"[DEBUG][dequeue_ready_step] step {step_id} not found in plan!")
        state["error"] = f"Step {step_id} not found in plan"
        state["finished"] = True
        state["step"] = None
        return state

    step["status"] = "running"
    task["plan"][step_id] = step
    print(f"[DEBUG][dequeue_ready_step] step[{step_id}] status set to 'running'")

    state["step"] = step
    print(f"[DEBUG][dequeue_ready_step] state['step'] set: {state['step']}")
    print(f"[DEBUG][dequeue_ready_step] state 반환 직전: {state}")
    return state