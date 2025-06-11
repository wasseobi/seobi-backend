from typing import Tuple, Literal
from app.langgraph.background.bg_state import BGState, PlanStep
from app.utils.openai_client import get_completion
from app.utils.prompt.autotask_prompt import TASK_RESULT_CONTENT_PROMPT
from datetime import datetime, timezone
import json
import re

def finalize_task_result(state: BGState) -> BGState:
    print(f"[DEBUG][finalize_task_result] state: {state}")
    task = state.get("task")
    print(f"[DEBUG][finalize_task_result] state['task']: {task}")
    if not task:
        state["error"] = "모든 AutoTask 완료"
        state["finished"] = True
        return state

    plan = task.get("plan", {})
    completed = task.get("completed_ids", [])
    ready_queue = task.get("ready_queue", [])
    print(f"[DEBUG][finalize_task_result] plan: {plan}")
    print(f"[DEBUG][finalize_task_result] completed: {completed}")
    print(f"[DEBUG][finalize_task_result] ready_queue: {ready_queue}")

    # 모든 Step이 완료되었는지 확인
    if len(completed) == len(plan) and not ready_queue:
        print("[finalize_task_result] 모든 Step 완료됨. 결과 정리 중...")

        # Step 결과 순서는 최초 실행 순서대로 → ready_queue 순서를 기록한 리스트 사용
        sorted_step_ids = [sid for sid in plan.keys() if sid in completed]
        print(f"[DEBUG][finalize_task_result] sorted_step_ids: {sorted_step_ids}")
        step_summaries = []
        step_outputs_for_llm = []

        for step_id in sorted_step_ids:
            step = plan[step_id]
            print(f"[DEBUG][finalize_task_result] step_id: {step_id}, step: {step}")
            summary_entry = {
                "step_id": step_id,
                "tool": step.get("tool"),
                "objective": step.get("objective"),
                "step_output": step.get("output")
            }
            step_summaries.append(summary_entry)

            step_outputs_for_llm.append(
                f"- [{step_id}] {step.get('objective')}: {step.get('output')}"
            )

        # 전체 요약 생성
        title = task.get("title", "")
        description = task.get("description", "")
        joined_outputs = "\n".join(step_outputs_for_llm)
        print(f"[DEBUG][finalize_task_result] title: {title}, description: {description}")
        print(f"[DEBUG][finalize_task_result] step_outputs_for_llm: {joined_outputs}")

        prompt = TASK_RESULT_CONTENT_PROMPT.format(
            title=title,
            description=description,
            step_outputs=joined_outputs
        )
        print(f"[DEBUG][finalize_task_result] prompt: {prompt}")

        messages = [
            {"role": "system", "content": "너는 전문 칼럼니스트야"},
            {"role": "user", "content": prompt}
        ]
        print(f"[DEBUG][finalize_task_result] messages: {messages}")

        try:
            response = get_completion(messages)
            print(f"[DEBUG][finalize_task_result] LLM 응답: {response}")
            
            if response and isinstance(response, str):
                summary = response.strip()  # 앞뒤 공백만 제거
            else:
                summary = "(최종 요약 없음)"
            
            print(f"[finalize_task_result][DEBUG] 파싱된 summary: {summary}")

        except Exception as e:
            print(f"[finalize_task_result] 요약 생성 실패: {str(e)}")
            summary = "(최종 요약 실패)"

        task["task_result"] = {
            "completed": True,
            "summary": summary,
            "steps": step_summaries
        }
        print(f"[DEBUG][finalize_task_result] task['task_result']: {task['task_result']}")
        task["finish_at"] = datetime.now(timezone.utc)
        print(f"[DEBUG][finalize_task_result] task['finish_at']: {task['finish_at']}")

        state["task"] = task
        state["finished"] = True
        print(f"[DEBUG][finalize_task_result] state 반환: {state}")

    return state
