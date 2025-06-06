from typing import Tuple, Dict, Any
from app.langgraph.background.bg_state import BGState, PlanStep
from app.langgraph.background.planners.tool_registry import get_tool_by_name
from app.langgraph.background.planners.format_tool_input import format_tool_input
from app.utils.summarize_output import gpt_summarize_output
import re

def run_tool(state: BGState, step: PlanStep) -> Tuple[BGState, PlanStep]:
    """
    주어진 PlanStep에 해당하는 tool을 실행하고 결과를 PlanStep에 저장한다.
    실행 결과는 step["output"]에 저장하며, 성공 여부에 따라 status를 변경한다.
    """
    task = state.get("task")
    if not task:
        state["error"] = "No task found"
        state["finished"] = True
        return state, step

    try:
        tool_name = step.get("tool")
        if not tool_name:
            raise ValueError(f"Missing tool in step {step['step_id']}")

        # 도구 함수 가져오기
        tool_fn = get_tool_by_name(tool_name)
        if not tool_fn:
            raise ValueError(f"Tool '{tool_name}' is not allowed or not found")

        # 선행 Step의 output → prior_outputs
        plan = task.get("plan", {})
        prior_outputs: Dict[str, Any] = {}
        for dep_id in step.get("depends_on", []):
            dep_step = plan.get(dep_id)
            if dep_step and "output" in dep_step:
                prior_outputs[dep_id] = dep_step["output"]

        # 도구 입력값 생성
        tool_input = format_tool_input(
            tool_name=tool_name,
            objective=step.get("objective", ""),
            prior_outputs=prior_outputs
        )

        def clean_key(k): return re.sub(r'[\s"\']', '', k)
        tool_input = {clean_key(k): v for k, v in tool_input.items()}

        # 예외 처리 (특정 도구 전용 설정)
        if tool_name == "google_news" and tool_input.get("tbs") == "qdr:d":
            tool_input["tbs"] = "qdr:m"

        step["tool_input"] = tool_input
        print(f"[run_tool] tool: {tool_name}, input: {tool_input}")

        # 도구 실행
        if hasattr(tool_fn, "invoke"):
            result = tool_fn.invoke(tool_input)
        else:
            result = tool_fn(**tool_input)

        # 결과 요약 후 저장
        step["output"] = gpt_summarize_output(
            output=result,
            tool_name=tool_name,
            objective=step.get("objective")
        )
        step["status"] = "done"
        print(f"[run_tool] output before evaluation: {step.get('output')}")

    except Exception as e:
        print(f"[run_tool] Error: {e}")
        step["status"] = "failed"
        step["output"] = {"error": str(e)}
        state["error"] = f"[{step['step_id']}] {str(e)}"

    # 상태 반영
    task["plan"][step["step_id"]] = step
    state["task"] = task

    return state, step
