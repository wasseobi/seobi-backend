from datetime import datetime, timezone
from app.langgraph.background.bg_state import BGState
from app.services.auto_task_service import AutoTaskService
import json

auto_task_service = AutoTaskService()

def write_result_to_db(state: BGState) -> BGState:
    """
    task_result를 AutoTask DB에 저장하고, 상태를 초기화합니다.
    """
    print(f"[DEBUG][write_result_to_db] state: {state}")
    task = state.get("task")
    print(f"[DEBUG][write_result_to_db] task: {task}")
    if not task:
        # 더 이상 처리할 task가 없을 때는 그냥 상태만 반환
        state["error"] = "모든 AutoTask 완료"
        state["finished"] = True
        return state

    task_id = task["task_id"]
    title = task["title"]
    result = task.get("task_result", {})
    finish_at = task.get("finish_at", datetime.now(timezone.utc))
    print(f"[DEBUG][write_result_to_db] task_id: {task_id}, title: {title}, result: {result}, finish_at: {finish_at}")

    result_str = json.dumps(result, ensure_ascii=False)

    # NOTE : DB에 저장 (테스트용), 변경 예정 (+ auto_task_service)
    try:
        print(f"[DEBUG][write_result_to_db] auto_task_service.save_result 호출")
        auto_task_service.background_save_result(
            task_id=task_id,
            result=result_str,
            finish_at=finish_at
        )
        print(f"[DEBUG][write_result_to_db] save_result 성공")
    except Exception as e:
        print(f"[DEBUG][write_result_to_db] save_result 예외: {e}")
        state["error"] = f"Failed to save task result: {str(e)}"
        state["task"] = task
        state["finished"] = True
        return state

    # state["finished"] = False   # NOTE: 모든 main + sub task 합쳐서 결과 만드는 노드 나오면 False 로 변경
    print(f"[DEBUG][write_result_to_db] state 반환: {state}")
    return state
