from typing import Literal
from app.langgraph.background.bg_state import BGState, PlanStep
from app.services.auto_task_service import AutoTaskService
from app.utils.auto_task_utils import get_current_step_message

auto_task_service = AutoTaskService()

def evaluate_step(state: BGState) -> BGState:
    """
    실행된 Step의 output을 평가하고 상태만 갱신합니다.
    실제 queue 정리는 mark_step_completed에서 수행됩니다.
    """
    task = state.get("task")
    step: PlanStep = state.get("step")
    step_id = step["step_id"]
    output = step.get("output", {})

    score = output.get("quality_score", 0.0)
    attempt = step.get("attempt", 0)
    max_attempt = step.get("max_attempt", 2)
    print(f"[evaluate_step] Step: {step_id}, Score: {score}, Attempt: {attempt}/{max_attempt}")

    # 평가 기준에 따른 상태 업데이트
    if score > 0.5:
        step["status"] = "done"
        status = "done"
    elif attempt < max_attempt:
        step["status"] = "pending"
        step["attempt"] = attempt + 1
        status = "pending"
        print(f"[evaluate_step] Retrying step {step_id} (attempt {attempt + 1})")
    else:
        step["status"] = "failed"
        status = "failed"
        state["error"] = f"Step {step_id} failed after {attempt} attempts (score={score})"
        print(f"[evaluate_step] step {step_id} 평가 실패 → status=failed")

    # 공통: status별 메시지 append & 저장
    tool = step.get("tool")
    auto_task_id = str(task["task_id"])
    msg = get_current_step_message(tool, status)
    history = state.get("current_step", [])
    history.append(msg)
    state["current_step"] = history
    print(f"[DEBUG][evaluate_step] current_step update: history={history}")
    auto_task_service.update(auto_task_id, current_step=history)

    # 상태 저장
    task["plan"][step_id] = step
    state["task"] = task
    state["step"] = step  # 다음 분기를 위해 다시 전달
    print(f"[evaluate_step] score={score}, attempt={attempt}, max_attempt={max_attempt}")
    print(f"[evaluate_step] step status = {step['status']}")

    return state