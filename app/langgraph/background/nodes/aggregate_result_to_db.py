from app.langgraph.background.bg_state import BGState
from app.services.auto_task_service import AutoTaskService
from app.utils.openai_client import get_completion
import json

auto_task_service = AutoTaskService()


AGGREGATE_MARKDOWN_REPORT_PROMPT = """
아래 단계별 업무 정보를 참고해서,
- 전체 내용을 종합해 마크다운(Markdown) 형식의 최종 업무 요약 리포트를 작성해줘.
- 제목, 목차, 소제목(섹션)을 output 내용에 따라 알아서 정하고,
- 각 단계(title/description/output)를 논리적으로 연결해 설명해.
- #, ##, -, 표 등 마크다운 문법을 적극 활용하고, 읽기 쉽고 자연스럽게 정리해.

단계별 정보(JSON):
{task_outputs}
"""

def aggregate_result_to_db(state: BGState) -> BGState:
    user_id = state.get("user_id")
    task_runtime = state.get("task")
    print(f"[DEBUG][aggregate_result_to_db] user_id: {user_id}, task_runtime: {task_runtime}")
    if not (user_id and task_runtime):
        state["error"] = "user_id 또는 task 정보 없음"
        state["finished"] = True
        return state

    all_tasks = auto_task_service.get_user_auto_tasks(user_id)
    anchor_task_id = str(task_runtime["task_id"])
    id_to_task = {str(t["id"]): t for t in all_tasks}

    task_outputs = []
    current_id = anchor_task_id
    main_task = None

    while current_id:
        task = id_to_task.get(current_id)
        if not task:
            print(f"[ERROR][aggregate_result_to_db] task_id={current_id}에 해당하는 task 없음!")
            break
        print(f"[DEBUG][aggregate_result_to_db] collecting: {task['title']} ({current_id})")
        task_outputs.append({
            "title": task["title"],
            "description": task.get("description", ""),
            "output": task.get("output", "")
        })
        # main이면 종료
        if not task.get("task_list"):
            main_task = task
            print(f"[DEBUG][aggregate_result_to_db] main task 도달: {main_task['title']} ({main_task['id']})")
            break
        main_title = task["task_list"][0]
        parent = next((t for t in all_tasks if t["title"] == main_title and not t.get("task_list")), None)
        if parent:
            current_id = str(parent["id"])
        else:
            print(f"[ERROR][aggregate_result_to_db] parent task({main_title})를 찾지 못함!")
            break

    if not main_task:
        state["error"] = "aggregate_result_to_db: main task 찾기 실패"
        state["finished"] = True
        return state

    # sub → ... → main 순이니 뒤집기(main→sub 순)
    task_outputs = task_outputs[::-1]
    print(f"[DEBUG][aggregate_result_to_db] task_outputs(역순): {json.dumps(task_outputs, ensure_ascii=False, indent=2)}")

    # json pretty format으로 넘기면 LLM이 더 잘 이해함
    task_outputs_json = json.dumps(task_outputs, ensure_ascii=False, indent=2)

    prompt = AGGREGATE_MARKDOWN_REPORT_PROMPT.format(task_outputs=task_outputs_json)
    print(f"[DEBUG][aggregate_result_to_db] prompt 생성 완료")
    messages = [
        {"role": "system", "content": "아래 프롬프트에 따라 마크다운 업무 리포트를 생성해줘. 반드시 예시 구조와 마크다운 스타일을 따르고, 논리적 연결성을 강조해."},
        {"role": "user", "content": prompt}
    ]
    error_response = "# 자동화 업무 요약 리포트\n(데이터 없음)"

    try:
        print(f"[DEBUG][aggregate_result_to_db] LLM 호출 시작")
        aggregate_result = get_completion(messages)
        if not aggregate_result:
            print(f"[WARN][aggregate_result_to_db] LLM 응답 없음, error_response 반환")
            aggregate_result = error_response
    except Exception as e:
        print(f"[ERROR][aggregate_result_to_db] LLM 리포트 생성 실패: {e}")
        aggregate_result = error_response

    try:
        print(f"[DEBUG][aggregate_result_to_db] main_task[{main_task['id']}]에 결과 저장")
        auto_task_service.update(main_task["id"], output=aggregate_result)
        print(f"[DEBUG][aggregate_result_to_db] DB 업데이트 성공")
    except Exception as e:
        print(f"[ERROR][aggregate_result_to_db] main task 업데이트 실패: {e}")
        state["error"] = f"aggregate_result_to_db: main task 업데이트 실패: {e}"
        state["finished"] = True
        return state

    if state.get("task"):
        state["task"]["task_result"] = aggregate_result

    state["task"] = None
    state["all_task_done"] = None
    state["step"] = None
    state["current_step"] = []
    state["finished"] = True
    return state
