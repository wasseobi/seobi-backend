from datetime import datetime, timezone
from app.langgraph.background.bg_state import BGState, TaskRuntime, PlanStep
from app.services.auto_task_service import AutoTaskService
import uuid

auto_task_service = AutoTaskService()

# NOTE: (juaa) auto_task의 task_list 가 1개만 들어가는 거면 text 여도 좋을 거 같아요.
def get_task_list_title(task):
    """
    task_list가 리스트이면 첫 번째 값 반환 (없으면 None)
    """
    task_list = task.get("task_list")
    if isinstance(task_list, list):
        return task_list[0] if task_list else None
    return None  # 혹시라도 None이면

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

    # 디버깅: 전체 task 현황 출력
    for t in auto_tasks:
        print(f"[DEBUG][auto_tasks] title: {t['title']}, status: {t['status']}, task_list: {t.get('task_list')} -> {get_task_list_title(t)}")

    # 1️⃣ 실행 가능한 서브 작업
    sub_candidates = [
        t for t in auto_tasks
        if t["status"] == "undone"
        and get_task_list_title(t)
        and any(
            prev["title"] == get_task_list_title(t) and prev["status"] == "done"
            for prev in auto_tasks
        )
    ]
    print(f"[DEBUG] sub_candidates: {[t['title'] for t in sub_candidates]}")
    if sub_candidates:
        selected = sub_candidates[0]
        now = datetime.now(timezone.utc)
        try:
            result = auto_task_service.update(
                selected["id"],
                start_at=now
            )
            print(f"[DEBUG] update 결과: {result}")
        except Exception as e:
            print(f"[ERROR] update 호출 실패: {e}")
        state["task"] = TaskRuntime(
            task_id=uuid.UUID(selected["id"]),
            title=selected["title"],
            description=selected["description"],
            task_list=selected.get("task_list"),
            plan={},
            ready_queue=[],
            completed_ids=[],
            task_result=None,
            start_at=now,
            finish_at=None
        )
        return state

    # 2️⃣ 실행 가능한 메인 작업 (task_list가 빈 리스트)
    main_candidates = [
        t for t in auto_tasks
        if t["status"] == "undone" and not get_task_list_title(t)
    ]
    print(f"[DEBUG] main_candidates: {[t['title'] for t in main_candidates]}")
    if main_candidates:
        selected = main_candidates[0]
        now = datetime.now(timezone.utc)
        auto_task_service.update(
            selected["id"],
            start_at=now
        )
        try:
            result = auto_task_service.update(
                selected["id"],
                start_at=now
            )
            print(f"[DEBUG] update 결과: {result}")
        except Exception as e:
            print(f"[ERROR] update 호출 실패: {e}")
        state["task"] = TaskRuntime(
            task_id=uuid.UUID(selected["id"]),
            title=selected["title"],
            description=selected["description"],
            task_list=selected.get("task_list"),
            plan={},
            ready_queue=[],
            completed_ids=[],
            task_result=None,
            start_at=now,
            finish_at=None
        )
        return state

    print("[DEBUG] 실행할 AutoTask 없음. 모든 작업 완료!")
    return state