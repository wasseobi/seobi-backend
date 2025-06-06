from datetime import datetime, timezone
from app.langgraph.background.bg_state import BGState, TaskRuntime, PlanStep
from app.services.auto_task_service import AutoTaskService
import uuid

auto_task_service = AutoTaskService()

def fetch_next_task(state: BGState) -> BGState:
    """
    다음 실행할 AutoTask를 선택한다.
    - 유저 전체 Task 중 status='undone' 우선순위에 따라 선택
    - 메인 Task → 서브 Task 순
    """
    if state.get("task") is not None:
        print("[DEBUG] fetch_next_task - 이미 task가 있음, 바로 반환")
        return state

    user_id = state.get("user_id")
    print(f"[DEBUG] fetch_next_task - user_id: {user_id}")
    if not user_id:
        print("[DEBUG] fetch_next_task - user_id 없음, 에러 반환")
        state["error"] = "Missing user_id in state"
        state["finished"] = True
        return state

    try:
        auto_tasks = auto_task_service.get_user_auto_tasks(user_id)  # 최신순 DESC 정렬된 상태로 반환
    except Exception as e:
        print(f"[DEBUG] fetch_next_task - get_user_auto_tasks 예외: {e}")
        state["error"] = str(e)
        state["finished"] = True
        return state

    # 가장 최근에 완료한 main task title
    last_title = state.get("last_completed_title")
    print(f"[DEBUG] fetch_next_task - last_completed_title: {last_title}")

    selected = None

    if last_title:
        # ✅ 1. sub_task 실행: 해당 main_task의 sub_task 중 undone이 있는지 확인
        sub_tasks = [
            t for t in auto_tasks
            if t["status"] == "undone" and t["task_list"] == last_title
        ]
        if sub_tasks:
            selected = sub_tasks[-1]
        else:
            # ✅ 모든 sub_task 완료됨 → 병합 노드로 가야 하는 시점
            print(f"[fetch_next_task] 모든 sub_task 완료됨: {last_title}")
            state["last_completed_title"] = None
            state["task"] = None
            state["finished"] = True
            return state

    if selected is None:
        # ✅ 2. 아직 시작한 main_task가 없거나 sub_task 다 끝났을 때 → 새 main_task 선택
        main_tasks = [
            t for t in auto_tasks
            if t["status"] == "undone" and (t["task_list"] is None or t["task_list"] == [])
        ]
        selected = main_tasks[-1] if main_tasks else None

    if selected:
        print(f"[DEBUG] fetch_next_task - 선택된 task: {selected}")
        state["task"] = TaskRuntime(
            task_id=uuid.UUID(selected["id"]),
            title=selected["title"],
            description=selected["description"],
            task_list=selected.get("task_list"),
            plan={},
            ready_queue=[],
            completed_ids=[],
            task_result=None,
            start_at=datetime.now(timezone.utc),
            finish_at=None
        )
    else:
        # ✅ 모든 main_task + sub_task 처리 완료
        print("[fetch_next_task] 모든 AutoTask 완료됨. 처리할 Task 없음.")
        # state["error"] = "No remaining AutoTask to process"
        # state["task"] = None
        # state["finished"] = True

    return state