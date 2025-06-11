from app.langgraph.background.bg_state import BGState, PlanStep

def mark_step_completed(state: BGState) -> BGState:
    """
    step 완료 또는 실패 시:
    - ready_queue에서는 무조건 제거
    - completed_ids에는 'done' 상태일 때만 추가
    """
    task = state.get("task")
    step = state.get("step")
    if not task or not step:
        state["error"] = "Invalid task or step in mark_step_completed"
        state["finished"] = True
        return state

    step_id = step.get("step_id")
    status = step.get("status")

    if status == "done":
        if step_id not in task.get("completed_ids", []):
            task.setdefault("completed_ids", []).append(step_id)

    if step_id in task.get("ready_queue", []):
        task["ready_queue"].remove(step_id)

    print(f"[DEBUG][mark_step_completed] step {step_id} ({status}) 처리됨. completed_ids={task.get('completed_ids')}, ready_queue={task.get('ready_queue')}")

    state["task"] = task
    state["step"] = None
    return state