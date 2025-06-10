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

    current_task = state.get("task")
    current_title = current_task["title"] if current_task else None
    current_group_title = current_title if current_task else None
    print(f"[DEBUG] current_group_title: {current_group_title}")

    # ✅ 현재 task가 있고, 더 이상 실행할 sub가 없다면 종료로 분기
    if current_task:
        next_sub_exists = any(
            t["status"] == "undone"
            and t.get("task_list")
            and t["task_list"][0] == current_group_title
            for t in auto_tasks
        )
        if not next_sub_exists:
            print("[DEBUG] 현재 main 그룹의 모든 작업 완료됨 → aggregate로 분기")
            state["task"] = None
            state["all_task_done"] = True
            return state      

    # 디버깅 전체 출력
    for t in auto_tasks:
        task_list = t.get("task_list") or []
        task_list_title = task_list[0] if task_list else None
        print(f"[DEBUG][auto_tasks] title: {t['title']}, status: {t['status']}, task_list: {task_list} -> {task_list_title}")

    # 실행 가능한 서브 작업 (현재 main 그룹에 속한)
    sub_candidates = [
        t for t in auto_tasks
        if t["status"] == "undone"
        and t.get("task_list")
        and t["task_list"][0] == current_group_title
    ]
    print(f"[DEBUG] sub_candidates: {[t['title'] for t in sub_candidates]}")
    if sub_candidates:
        selected = sub_candidates[0]
        now = datetime.now(timezone.utc)
        try:
            result = auto_task_service.update(selected["id"], start_at=now)
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

    # 실행 가능한 메인 작업 (처음 시작할 때만 가능)
    main_candidates = [
        t for t in auto_tasks
        if t["status"] == "undone" and not (t.get("task_list"))
    ]
    print(f"[DEBUG] main_candidates: {[t['title'] for t in main_candidates]}")
    if main_candidates:
        selected = main_candidates[0]
        now = datetime.now(timezone.utc)
        try:
            result = auto_task_service.update(selected["id"], start_at=now)
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
    state["task"] = None
    state["finished"] = True
    return state