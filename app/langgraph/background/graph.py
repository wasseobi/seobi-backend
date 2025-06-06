# app/langgraph/background/graph.py

from langgraph.graph import StateGraph
from app.langgraph.background.bg_state import BGState, PlanStep
from app.langgraph.background.nodes.fetch_next_task import fetch_next_task
from app.langgraph.background.nodes.initialize_task_plan import initialize_task_plan
from app.langgraph.background.nodes.dequeue_ready_step import dequeue_ready_step
from app.langgraph.background.nodes.run_tool import run_tool
from app.langgraph.background.nodes.evaluate_step import evaluate_step
from app.langgraph.background.nodes.finalize_task_result import finalize_task_result
from app.langgraph.background.nodes.write_result_to_db import write_result_to_db
from app.langgraph.background.edges.bg_edges import route_after_dequeue, route_after_evaluation

def get_background_graph() -> StateGraph:
    builder = StateGraph(BGState)

    builder.add_node("fetch_next_task", fetch_next_task)
    builder.add_node("initialize_task_plan", initialize_task_plan)
    builder.add_node("dequeue_ready_step", dequeue_ready_step)
    builder.add_node("run_tool", run_tool)
    builder.add_node("evaluate_step", evaluate_step)
    builder.add_node("finalize_task_result", finalize_task_result)
    builder.add_node("write_result_to_db", write_result_to_db)

    # Entry와 Finish가 동일한 이유:
    # fetch_next_task → 서브태스크를 반복적으로 처리 후, 메인 태스크 종료 판단 용도
    builder.set_entry_point("fetch_next_task")
    builder.set_finish_point("fetch_next_task")

    builder.add_edge("fetch_next_task", "initialize_task_plan")
    builder.add_edge("initialize_task_plan", "dequeue_ready_step")
    builder.add_conditional_edges("dequeue_ready_step", route_after_dequeue, {
        "run_tool": "run_tool",
        "finalize": "finalize_task_result"
    })
    builder.add_edge("run_tool", "evaluate_step")
    builder.add_conditional_edges("evaluate_step", route_after_evaluation, {
        "success": "dequeue_ready_step",
        "retry": "run_tool",                # NOTE: retry 될 때 tool_input 업데이트 돼서 되도록 하기
        "fail": "finalize_task_result"
    })
    builder.add_edge("finalize_task_result", "write_result_to_db")
    builder.add_edge("write_result_to_db", "fetch_next_task")

    return builder.compile()
