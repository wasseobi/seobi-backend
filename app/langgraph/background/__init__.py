# # background_nodes.py
# from typing import Optional
# from datetime import datetime
# from BackgroundState import BGState, TaskRuntime, PlanStep
# import uuid



# # ------------------------------------------
# # 5. evaluate_step
# # ------------------------------------------
# def evaluate_step(state: BGState, step_id: str) -> str:
#     from evaluator import evaluate_output

#     step = state["task"]["plan"][step_id]
#     score = evaluate_output(step["output"])
#     step["score"] = score
#     step["status"] = "done" if score >= 0.8 else "failed"
#     return step["status"]


# # ------------------------------------------
# # 8. finalize_task_result
# # ------------------------------------------
# def finalize_task_result(state: BGState) -> BGState:
#     from aggregator import aggregate_results

#     task = state["task"]
#     task["task_result"] = aggregate_results(task["plan"])
#     return state


# # ------------------------------------------
# # 9. write_result_to_db
# # ------------------------------------------
# def write_result_to_db(state: BGState) -> BGState:
#     from database import write_task_result

#     task = state["task"]
#     write_task_result(
#         task_id=task["id"],
#         result=task["task_result"],
#         finished_at=datetime.utcnow()
#     )
#     state["last_completed_title"] = task["title"]
#     state["task"] = None
#     return state


# # ------------------------------------------
# # 10. check_next_task
# # ------------------------------------------
# def check_next_task(state: BGState) -> BGState:
#     from database import has_remaining_tasks

#     if not has_remaining_tasks():
#         state["finished"] = True
#     return state
