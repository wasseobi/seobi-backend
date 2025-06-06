import uuid
from pprint import pprint
from app.langgraph.background.graph import build_background_graph
from app.langgraph.background.bg_state import BGState
from app import create_app


def run():
    app = create_app()
    with app.app_context():
        # DB URI 등 각종 설정, 모델, 서비스 다 사용 가능
        print("[DEBUG] DB URI:", app.config.get("SQLALCHEMY_DATABASE_URI"))
        graph = build_background_graph()

        # ✅ 1. 초기 상태 정의
        state = BGState(
            user_id=uuid.UUID("904c10cb-f4f1-4c32-b56f-331af20777df"),
            task=None,
            last_completed_title=None,
            error=None,
            finished=False,
            step=None
        )

        round_count = 0

        # ✅ 2. LangGraph 반복 실행
        while True:
            print(f"\n[🚀 실행 라운드 {round_count + 1}]")
            state = graph.invoke(state, config={"recursion_limit": 50})

            if state.get("error"):
                print(f"[❌ 오류 발생] {state['error']}")

            if state.get("finished") or state.get("error") == "No remaining AutoTask to process":
                print("\n[✅ 모든 Task 완료 또는 중단됨]")
                break

            round_count += 1

        # ✅ 3. 최종 상태 출력
        print("\n[✅ 최종 상태 출력]")
        pprint(state)

        # ✅ 4. 요약 결과 출력 (task가 있고, task_result도 있을 때만)
        if state.get("task") and state["task"].get("task_result"):
            print("\n🧾 [최종 요약 결과]")
            pprint(state["task"]["task_result"])


if __name__ == "__main__":
    run()
