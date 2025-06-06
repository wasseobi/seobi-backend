import uuid
from pprint import pprint
from app.langgraph.background.graph import get_background_graph
from app.langgraph.background.bg_state import BGState


def run():
    graph = get_background_graph()

    # ✅ 1. 초기 상태 정의
    state = BGState(
        user_id=uuid.UUID("af553404-7b43-413a-9caf-06d2e2495d8c"),
        task=None,
        last_completed_title=None,
        error=None,
        finished=False
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

    # ✅ 4. 요약 결과 출력
    if "task" in state and state["task"].get("task_result"):
        print("\n🧾 [최종 요약 결과]")
        pprint(state["task"]["task_result"])


if __name__ == "__main__":
    run()
