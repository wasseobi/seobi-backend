# app/langgraph/background/bg_edges.py

from typing import Literal, Optional
from app.langgraph.background.bg_state import BGState, PlanStep

def route_after_dequeue(state: BGState) -> Literal["run_tool", "finalize"]:
    """
    분기 조건:
    - step이 있으면 run_tool
    - step이 없으면 finalize_task_result
    """
    print(f"[DEBUG][route_after_dequeue] state: {state}")
    step = state.get("step")
    print(f"DEBUG: route_after_dequeue step: {step}, type: {type(step)}")
    print(f"DEBUG: step is truthy? {bool(step)}")
    if step:
        print("run_tool로 갑니다.")
        return "run_tool"
    else:
        print("finalize로 갑니다.")
        return "finalize"
    # return "run_tool" if step else "finalize"

def route_after_evaluation(state: BGState) -> Literal["success", "retry", "fail"]:
    step: PlanStep = state.get("step", {})
    status = step.get("status", "")
    print(f"[route_after_evaluation] step_id = {step.get('step_id')}, status = {status}")

    if status == "done":
        return "success"
    elif status == "pending":
        return "retry"
    else:
        return "fail"
