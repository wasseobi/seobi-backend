from langgraph.graph import StateGraph, START, END
from langgraph.checkpoint.memory import InMemorySaver
from langgraph.store.memory import InMemoryStore

from src.state import ChatState
from src.nodes import (
    parse_intent,
    generate_reply,
    save_dialogue,
    task_decision,
    call_tool
)

""" 상태 초기화 """
# def cast_to_dict(x):
#     """ChatState 객체를 딕셔너리로 변환"""
#     if isinstance(x, dict):
#         return x
#     if isinstance(x, ChatState):
#         return {
#             "user_input": x.user_input,
#             "parsed_intent": x.parsed_intent,
#             "reply": x.reply,
#             "action_required": x.action_required,
#             "executed_result": x.executed_result,
#             "timestamp": x.timestamp,
#             "user_id": x.user_id,
#             "messages": x.messages
#         }
#     return x

builder = StateGraph(dict)

""" 노드 추가 """
builder.add_node("parse_intent", parse_intent)     # 의도 분석
builder.add_node("generate_reply", generate_reply)  # 응답 생성
builder.add_node("save_dialogue", save_dialogue)    # 대화 저장
builder.add_node("task_decision", task_decision)    # 작업 필요 여부 판단
builder.add_node("execute_action", call_tool)       # 외부 도구 실행

""" 노드 간 연결 """
# 시작 -> 의도 분석
builder.add_edge(START, "parse_intent")

# 의도 분석 -> 응답 생성
builder.add_edge("parse_intent", "generate_reply")

# 응답 생성 -> 대화 저장
builder.add_edge("generate_reply", "save_dialogue")

# 대화 저장 -> 작업 판단 (무한 루프 방지 위해 삭제)
# builder.add_edge("save_dialogue", "task_decision")

# 작업 판단 -> 조건부 분기 (작업 실행 또는 종료)
builder.add_conditional_edges(
    "task_decision",
    lambda x: "execute_action" if x["action_required"] else END,
    ["execute_action", END]
)

# 작업 실행 -> 결과 응답 생성
builder.add_edge("execute_action", "generate_reply")
# 결과 응답 생성 -> 대화 저장
builder.add_edge("generate_reply", "save_dialogue")
# 대화 저장 -> END
builder.add_edge("save_dialogue", END)

""" 그래프 컴파일 """
checkpointer = InMemorySaver()
store = InMemoryStore()
graph = builder.compile(checkpointer, store=store)
