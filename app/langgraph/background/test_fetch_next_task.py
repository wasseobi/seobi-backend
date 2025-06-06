import uuid
from app.langgraph.background.nodes.fetch_next_task import fetch_next_task
from app.langgraph.background.nodes.initialize_task_plan import initialize_task_plan
from app.langgraph.background.nodes.dequeue_ready_step import dequeue_ready_step
from app.langgraph.background.nodes.run_tool import run_tool
from app.langgraph.background.nodes.evaluate_step import evaluate_step
from app.langgraph.background.nodes.finalize_task_result import finalize_task_result
from app.langgraph.background.bg_state import BGState
from app import create_app

# def test_fetch_next_task_main_task():
#     # 실제 존재하는 유저 UUID로 교체하세요
#     user_id = uuid.UUID("904c10cb-f4f1-4c32-b56f-331af20777df")
#     state: BGState = {
#         "user_id": user_id,
#         "task": None,
#         "last_completed_title": None,
#         "error": None,
#         "finished": False
#     }
#     app = create_app()
#     with app.app_context():
#         result = fetch_next_task(state)
#         print("result=", result)
#     # 실제 DB 상황에 따라 assert를 조정하세요
#     # 예시: assert result["task"] is not None
#     # assert result["task"]["title"] == "..."
    
# def test_initialize_task_plan_after_fetch():
#     user_id = uuid.UUID("904c10cb-f4f1-4c32-b56f-331af20777df")
#     state: BGState = {
#         "user_id": user_id,
#         "task": None,
#         "last_completed_title": None,
#         "error": None,
#         "finished": False
#     }
#     app = create_app()
#     with app.app_context():
#         result = fetch_next_task(state)
#         print("fetch_next_task result=", result)
#         if result["task"] is not None:
#             result2 = initialize_task_plan(result)
#             print("initialize_task_plan result=", result2)
#             # 검증: ready_queue에 step이 1개 이상 들어갔는지, plan이 비어있지 않은지
#             assert "ready_queue" in result2["task"]
#             assert isinstance(result2["task"]["ready_queue"], list)
#             assert len(result2["task"]["ready_queue"]) > 0, "ready_queue가 비어있지 않아야 합니다."
#             assert "plan" in result2["task"]
#             assert isinstance(result2["task"]["plan"], dict)
#             assert len(result2["task"]["plan"]) > 0, "plan이 비어있지 않아야 합니다."
#         else:
#             print("No task to initialize plan for.")

# def test_dequeue_ready_step_after_plan():
#     user_id = uuid.UUID("904c10cb-f4f1-4c32-b56f-331af20777df")
#     state: BGState = {
#         "user_id": user_id,
#         "task": None,
#         "last_completed_title": None,
#         "error": None,
#         "finished": False
#     }
#     app = create_app()
#     with app.app_context():
#         result = fetch_next_task(state)
#         if result["task"] is not None:
#             result2 = initialize_task_plan(result)
#             print("initialize_task_plan result=", result2)
#             state_after_plan = result2
#             state_after_dequeue, step = dequeue_ready_step(state_after_plan)
#             print("dequeue_ready_step result state=", state_after_dequeue)
#             print("dequeue_ready_step result step=", step)
#             # 검증: step이 None이 아니고, status가 'running'인지
#             assert step is not None, "ready_queue에서 step을 꺼내야 합니다."
#             assert step["status"] == "running", "dequeue된 step의 status는 'running'이어야 합니다."
#         else:
#             print("No task to initialize plan for.")

# def test_run_tool_after_dequeue():
#     user_id = uuid.UUID("904c10cb-f4f1-4c32-b56f-331af20777df")
#     state: BGState = {
#         "user_id": user_id,
#         "task": None,
#         "last_completed_title": None,
#         "error": None,
#         "finished": False
#     }
#     app = create_app()
#     with app.app_context():
#         result = fetch_next_task(state)
#         if result["task"] is not None:
#             result2 = initialize_task_plan(result)
#             print("initialize_task_plan=", result2)
#             state_after_plan = result2
#             state_after_dequeue, step = dequeue_ready_step(state_after_plan)
#             if step is not None:
#                 state_after_run, step_after_run = run_tool(state_after_dequeue, step)
#                 print("run_tool result state=", state_after_run)
#                 print("run_tool result step=", step_after_run)
#                 print(f"[run_tool] state: {state}")
#                 print(f"[run_tool] step: {step}")
#                 # 검증: step의 status가 'done' 또는 'failed'이고, output이 존재하는지
#                 assert step_after_run["status"] in ("done", "failed"), "run_tool 실행 후 status는 'done' 또는 'failed'여야 합니다."
#                 assert "output" in step_after_run, "run_tool 실행 후 output이 있어야 합니다."
#             else:
#                 print("No step to run tool for.")
#         else:
#             print("No task to initialize plan for.")

# def test_evaluate_step_after_run_tool():
#     user_id = uuid.UUID("904c10cb-f4f1-4c32-b56f-331af20777df")
#     state: BGState = {
#         "user_id": user_id,
#         "task": None,
#         "last_completed_title": None,
#         "error": None,
#         "finished": False
#     }
#     app = create_app()
#     with app.app_context():
#         result = fetch_next_task(state)
#         if result["task"] is not None:
#             result2 = initialize_task_plan(result)
#             state_after_plan = result2
#             state_after_dequeue, step = dequeue_ready_step(state_after_plan)
#             if step is not None:
#                 state_after_run, step_after_run = run_tool(state_after_dequeue, step)
#                 print("run_tool result state=", state_after_run)
#                 print("run_tool result step=", step_after_run)
#                 # evaluate_step 테스트
#                 state_after_eval, eval_status = evaluate_step(state_after_run, step_after_run)
#                 print("evaluate_step result state=", state_after_eval)
#                 print("evaluate_step result eval_status=", eval_status)
#                 # 검증: eval_status가 'success', 'retry', 'fail' 중 하나인지
#                 assert eval_status in ("success", "retry", "fail"), "evaluate_step 결과가 올바르지 않습니다."
#                 # step의 status가 올바르게 변경되었는지
#                 plan = state_after_eval["task"]["plan"]
#                 step_eval = plan[step_after_run["step_id"]]
#                 if eval_status == "success":
#                     assert step_eval["status"] == "done"
#                 elif eval_status == "retry":
#                     assert step_eval["status"] == "pending"
#                 elif eval_status == "fail":
#                     assert step_eval["status"] == "failed"
#             else:
#                 print("No step to run tool for.")
#         else:
#             print("No task to initialize plan for.")

def test_full_task_execution_loop():
    user_id = uuid.UUID("904c10cb-f4f1-4c32-b56f-331af20777df")
    state: BGState = {
        "user_id": user_id,
        "task": None,
        "last_completed_title": None,
        "error": None,
        "finished": False
    }
    app = create_app()
    with app.app_context():
        # 1. fetch_next_task
        state = fetch_next_task(state)
        assert state["task"] is not None, "Task가 존재해야 합니다."
        # 2. initialize_task_plan
        state = initialize_task_plan(state)
        assert "ready_queue" in state["task"] and len(state["task"]["ready_queue"]) > 0, "ready_queue가 비어있지 않아야 합니다."
        # 3. 루프: 모든 step 완료까지 반복
        while True:
            # dequeue_ready_step
            result = dequeue_ready_step(state)
            # finalize_task_result 등은 (state, result_status) 튜플을 반환할 수 있으므로 분기 처리
            if isinstance(result, tuple):
                state = result[0]
            else:
                state = result
            step = state.get("step")
            if step is None:
                print("[test_full_task_execution_loop] 모든 step 완료, finalize_task_result로 분기")
                break
            # run_tool
            result = run_tool(state, step)
            if isinstance(result, tuple):
                state = result[0]
            else:
                state = result
            step = state.get("step")
            # evaluate_step
            result = evaluate_step(state)
            if isinstance(result, tuple):
                state = result[0]
            else:
                state = result
            eval_status = state.get("eval_status")
            print(f"[test_full_task_execution_loop] step {step['step_id']} 평가 결과: {eval_status}")
            if eval_status == "success":
                # 성공 시 다음 step으로 루프 계속
                continue
            elif eval_status == "retry":
                # 재시도 예약: pending 상태로 다시 run_tool로 루프
                continue
            elif eval_status == "fail":
                # 완전 실패: 루프 종료
                print(f"[test_full_task_execution_loop] step {step['step_id']} 완전 실패, 루프 종료")
                break
        # 모든 step 완료 후 상태 검증
        assert state["task"] is not None
        print("[test_full_task_execution_loop] 최종 state=", state)

def test_finalize_task_result_after_full_loop():
    user_id = uuid.UUID("904c10cb-f4f1-4c32-b56f-331af20777df")
    state: BGState = {
        "user_id": user_id,
        "task": None,
        "last_completed_title": None,
        "error": None,
        "finished": False
    }
    app = create_app()
    with app.app_context():
        # 1. fetch_next_task
        state = fetch_next_task(state)
        assert state["task"] is not None, "Task가 존재해야 합니다."
        # 2. initialize_task_plan
        state = initialize_task_plan(state)
        assert "ready_queue" in state["task"] and len(state["task"]["ready_queue"]) > 0, "ready_queue가 비어있지 않아야 합니다."
        # 3. 루프: 모든 step 완료까지 반복
        while True:
            state = dequeue_ready_step(state)
            step = state.get("step")
            if step is None:
                break
            state = run_tool(state)
            state = evaluate_step(state)
            eval_status = state.get("eval_status")
            if eval_status == "fail":
                break
        # 4. 모든 step 완료 후 finalize_task_result 호출
        state, result_status = finalize_task_result(state)
        print("[test_finalize_task_result_after_full_loop] result_status=", result_status)
        print("[test_finalize_task_result_after_full_loop] 최종 state=", state)
        # 검증: task_result가 생성되어 있는지
        assert state["task"].get("task_result") is not None, "task_result가 생성되어야 합니다."
        assert state["finished"] is True, "finished가 True여야 합니다."

def test_finalize_task_result_summary_content():
    user_id = uuid.UUID("904c10cb-f4f1-4c32-b56f-331af20777df")
    state: BGState = {
        "user_id": user_id,
        "task": None,
        "last_completed_title": None,
        "error": None,
        "finished": False
    }
    app = create_app()
    with app.app_context():
        # 1. fetch_next_task
        state = fetch_next_task(state)
        assert state["task"] is not None, "Task가 존재해야 합니다."
        # 2. initialize_task_plan
        state = initialize_task_plan(state)
        assert "ready_queue" in state["task"] and len(state["task"]["ready_queue"]) > 0, "ready_queue가 비어있지 않아야 합니다."
        # 3. 루프: 모든 step 완료까지 반복
        while True:
            state = dequeue_ready_step(state)
            step = state.get("step")
            if step is None:
                break
            state = run_tool(state)
            state = evaluate_step(state)
            eval_status = state.get("eval_status")
            if eval_status == "fail":
                break
        # 4. 모든 step 완료 후 finalize_task_result 호출
        state, result_status = finalize_task_result(state)
        print("[test_finalize_task_result_summary_content] result_status=", result_status)
        print("[test_finalize_task_result_summary_content] 최종 state=", state)
        # 검증: summary가 비어있지 않고 string 또는 list가 아닌지 확인
        task_result = state["task"].get("task_result")
        assert task_result is not None, "task_result가 생성되어야 합니다."
        summary = task_result.get("summary")
        assert summary is not None, "summary가 None이 아니어야 합니다."
        print(f"[test_finalize_task_result_summary_content] summary type: {type(summary)}, value: {summary}")
        # summary가 dict면 value가 string이고 비어있지 않은지 확인
        if isinstance(summary, dict):
            assert len(list(summary.values())[0].strip()) > 0, "summary dict의 value가 비어있지 않아야 합니다."
        elif isinstance(summary, str):
            assert len(summary.strip()) > 0, "summary가 비어있지 않아야 합니다."
        elif isinstance(summary, list):
            assert any(len(str(s).strip()) > 0 for s in summary), "summary 리스트가 비어있지 않아야 합니다."
        else:
            assert False, f"summary 타입이 예상과 다름: {type(summary)}"

test_full_task_execution_loop()
test_finalize_task_result_after_full_loop()
test_finalize_task_result_summary_content()
