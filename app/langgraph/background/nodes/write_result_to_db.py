from datetime import datetime, timezone
from app.langgraph.background.bg_state import BGState
from app.services.auto_task_service import AutoTaskService

auto_task_service = AutoTaskService()

def write_result_to_db(state: BGState) -> BGState:
    """
    task_result를 AutoTask DB에 저장하고, 상태를 초기화합니다.
    """
    task = state.get("task")
    if not task:
        return {
            **state,
            "error": "No task to write"
        }

    task_id = task["task_id"]
    title = task["title"]
    result = task.get("task_result", {})
    finish_at = task.get("finish_at", datetime.now(timezone.utc))

    # NOTE : DB에 저장 (테스트용), 변경 예정 (+ auto_task_service)
    try:
        auto_task_service.save_result(
            task_id=task_id,
            result=result,
            finish_at=finish_at
        )
    except Exception as e:
        return {
            **state,
            "error": f"Failed to save task result: {str(e)}"
        }

    # ✅ 상태 초기화 및 다음 Task 준비
    return {
        **state,
        "last_completed_title": title,
        "task": None,
        "finished": False
    }
