# app/langgraph/background/bg_edges.py

from typing import Literal, Optional
from app.langgraph.background.bg_state import BGState, PlanStep

def route_after_dequeue(state: BGState) -> Literal["run_tool", "finalize"]:
    """
    분기 조건:
    - step이 있으면 run_tool
    - step이 없으면 finalize_task_result
    """
    step = state.get("step")
    return "run_tool" if step else "finalize"

def route_after_evaluation(state: BGState, step: PlanStep) -> Literal["success", "retry", "fail"]:
    """
    실행된 Step의 평가 상태(status)에 따라 분기 방향을 결정.
    - status == "done"  → success
    - status == "pending" → retry
    - 그 외 (failed 등) → fail
    """
    status = step.get("status", "")
    if status == "done":
        return "success"
    elif status == "pending":
        return "retry"
    else:
        return "fail"