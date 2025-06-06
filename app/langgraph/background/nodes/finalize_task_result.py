from typing import Tuple, Literal
from app.langgraph.background.bg_state import BGState, PlanStep
from app.utils.openai_client import get_openai_client, get_completion
from datetime import datetime, timezone
import json
import re

TASK_RESULT_CONTENT_PROMPT = """
너는 다양한 주제에 대해 정돈된 설명형 콘텐츠를 작성하는 전문 칼럼니스트야.

사용자는 어떤 주제를 조사하거나 정리하기 위해 여러 개의 AI 도구를 순차적으로 사용했고,  
각 도구는 그 단계의 목적에 따라 실행되었고, 실행 결과는 아래에 정리돼 있어.

step_outputs는 다음과 같은 형식으로 각 단계의 정보가 정리돼 있어:
- 순서: [사용한 도구 이름] 해당 단계의 목적: 실행 결과 요약  
- 예시: [google_news] Microsoft Azure 최신 동향 수집: {{'summary': [...], 'quality_score': 0.9}}

이 step_outputs는 단순 나열이 아니라, 사용자가 하나의 주제(title)에 대해 조사하고 의도한 목표(description)에 도달하기 위한 흐름 그 자체야.  
각 step은 독립적으로 보지 말고, 순서와 연결 관계 속에서 의미를 파악해야 해.  

너의 역할은 단순한 요약이 아니라, 사용자의 목표(description)에 정확히 부합하는 콘텐츠를 **하나의 짧은 칼럼처럼** 정돈해서 작성하는 거야.

작성 기준:
- 반드시 사용자의 목표(description)을 중심 기준으로 삼아야 하며, 이 목적에 부합하지 않는 정보는 제거해야 해
- step_outputs 간의 흐름과 관계를 고려하여 연결된 내용으로 정리해
- 목적과 관련 없는 정보는 배제하고, 핵심만 남겨
- 단편적인 요약이 아니라, 주제를 설명하는 3~5문장의 자연스러운 단락을 작성해
- bullet 형식이나 표 형식은 사용하지 마
- 마치 주제를 정리한 브리핑 칼럼처럼 읽히도록 해줘

이 글은 하나의 짧은 콘텐츠로 독자에게 전달될 수 있어야 해.  
정보를 나열하는 게 아니라, 목적에 맞는 내용을 문맥 있게 전달하는 것이 가장 중요해.

────────────────────────────────────
콘텐츠 주제: {title}
사용자의 목적: {description}
AI 도구 실행 결과 요약 (step_outputs): {step_outputs}
────────────────────────────────────

출력 형식:
- 전체 결과를 JSON으로 출력
- key는 "summary"
- value는 설명형 단락(string)
- JSON 형식 오류 없이 정확히 출력할 것

반드시 아래와 같은 JSON 형식으로 출력해:
```json
{{
    "summary": "..."
}}

출력 예시:
```json
{{
  "summary": "Microsoft Azure는 인공지능 기술과 클라우드 인프라를 통합하며, 최신 IT 산업에서 전략적 입지를 더욱 강화하고 있다. ..."
}}
"""

def finalize_task_result(state: BGState) -> BGState:
    task = state.get("task")
    if not task:
        state["error"] = "No task found"
        state["finished"] = True
        return state

    plan = task.get("plan", {})
    completed = task.get("completed_ids", [])
    ready_queue = task.get("ready_queue", [])

    # 모든 Step이 완료되었는지 확인
    if len(completed) == len(plan) and not ready_queue:
        print("[finalize_task_result] 모든 Step 완료됨. 결과 정리 중...")

        # Step 결과 순서는 최초 실행 순서대로 → ready_queue 순서를 기록한 리스트 사용
        sorted_step_ids = [sid for sid in plan.keys() if sid in completed]
        step_summaries = []
        step_outputs_for_llm = []

        for step_id in sorted_step_ids:
            step = plan[step_id]
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

        prompt = TASK_RESULT_CONTENT_PROMPT.format(
            title=title,
            description=description,
            step_outputs=joined_outputs
        )

        messages = [
            {"role": "system", "content": "너는 전문 칼럼니스트야"},
            {"role": "user", "content": prompt}
        ]

        client = get_openai_client()
        try:
            response = get_completion(client, messages)
            match = re.search(r'```json\s*({[\s\S]*?})\s*```', response)
            if not match:
                # ```json ... ``` 블록이 없으면 그냥 JSON 오브젝트만 추출
                match = re.search(r'({[\s\S]*})', response)

            if match:
                response_json = json.loads(match.group(1))
                print(f"[finalize_task_result][DEBUG] LLM JSON 응답: {response_json}")
                if "summary" in response_json and isinstance(response_json["summary"], str):
                    summary = response_json["summary"]
                else:
                    summary = "(최종 요약 없음)"
                print(f"[finalize_task_result][DEBUG] 파싱된 summary: {summary}")

            else:
                print(f"[finalize_task_result][DEBUG] LLM 응답에서 JSON 블록 파싱 실패: {response}")
                summary = "(최종 요약 파싱 실패)"

        except Exception as e:
            print(f"[finalize_task_result] 요약 생성 실패: {str(e)}")
            summary = {"summary": "(최종 요약 실패)"}

        task["task_result"] = {
            "completed": True,
            "summary": summary,
            "steps": step_summaries
        }
        task["finish_at"] = datetime.now(timezone.utc)

        state["task"] = task
        state["finished"] = True

    return state
