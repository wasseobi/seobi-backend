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

    print(f"[DEBUG][dequeue_ready_step] ready_queue: {ready_queue}")
    print(f"[DEBUG][dequeue_ready_step] completed_ids: {task.get('completed_ids')}")

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

    # ✅ 이미 완료된 step이면 다시 실행시키지 않음
    if step.get("status") == "done":
        print(f"[DEBUG][dequeue_ready_step] step {step_id} is already done. Skipping.")
        task["ready_queue"].remove(step_id)
        state["task"] = task
        state["step"] = None
        return state

    step["status"] = "running"
    task["plan"][step_id] = step

    # ✅ current_step이 None일 경우 초기화
    history = state.get("current_step")
    if history is None:
        print("[DEBUG][dequeue_ready_step] current_step가 None → 빈 리스트로 초기화")
        history = []
    else:
        print(f"[DEBUG][dequeue_ready_step] current_step 기존 상태: {history}")

    # BGState(current_step)에만 append + 디버그 메시지
    tool = step.get("tool")
    status = step.get("status")
    msg = get_current_step_message(tool, status)
    
    history.append(msg)
    state["current_step"] = history
    print(f"[DEBUG][dequeue_ready_step] current_step update: history={history}")

    state["task"] = task
    state["step"] = step
    return state