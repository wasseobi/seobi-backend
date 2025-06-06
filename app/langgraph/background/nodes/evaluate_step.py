from typing import Literal
from app.langgraph.background.bg_state import BGState, PlanStep

def evaluate_step(state: BGState) -> BGState:
    """
    실행된 Step의 output을 평가하고, 상태만 갱신합니다.
    실제 분기는 route_after_evaluation에서 처리합니다.
    """
    task = state.get("task")
    step: PlanStep = state.get("step")  # step은 Tuple 반환 구조에서 전달됨
    step_id = step["step_id"]
    output = step.get("output", {})

    score = output.get("quality_score", 0.0)
    attempt = step.get("attempt", 0)
    max_attempt = step.get("max_attempt", 2)

    print(f"[evaluate_step] Step: {step_id}, Score: {score}, Attempt: {attempt}/{max_attempt}")

    if score > 0.5:
        step["status"] = "done"
        if step_id not in task.get("completed_ids", []):
            task.setdefault("completed_ids", []).append(step_id)
        if step_id in task.get("ready_queue", []):
            task["ready_queue"].remove(step_id)

    elif attempt < max_attempt:
        step["status"] = "pending"
        step["attempt"] = attempt + 1
        print(f"[evaluate_step] Retrying step {step_id} (attempt {attempt + 1})")

    else:
        step["status"] = "failed"
        state["error"] = f"Step {step_id} failed after {attempt} attempts (score={score})"

    task["plan"][step_id] = step
    state["task"] = task
    state["step"] = step  # 다음 분기를 위해 다시 전달
    print(f"[evaluate_step] score={score}, attempt={attempt}, max_attempt={max_attempt}")
    print(f"[evaluate_step] step status = {step['status']}")

    return state