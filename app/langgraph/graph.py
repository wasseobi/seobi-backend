"""LangGraph 기반의 대화 그래프를 정의하는 모듈입니다."""
from langgraph.graph import StateGraph, START, END
from langgraph.checkpoint.memory import InMemorySaver
from langgraph.store.memory import InMemoryStore

from app.langgraph.state import ChatState
from app.langgraph.nodes import (
    parse_intent,
    generate_reply,
    task_decision,
    call_tool
)

builder = StateGraph(ChatState)

# 노드 추가
builder.add_node("parse_intent", parse_intent)     # 의도 분석
builder.add_node("task_decision", task_decision)   # 작업 필요 여부 판단
builder.add_node("execute_action", call_tool)      # 외부 도구 실행
builder.add_node("generate_reply", generate_reply) # 응답 생성

# 엣지 설정
# 시작 -> 의도 분석
builder.add_edge(START, "parse_intent")

# 의도 분석 -> 작업 판단
builder.add_edge("parse_intent", "task_decision")

# 작업 판단 -> 조건부 분기
builder.add_conditional_edges(
    "task_decision",
    lambda x: "execute_action" if x["action_required"] else "generate_reply",
    ["execute_action", "generate_reply"]
)

# 작업 실행 -> 응답 생성
builder.add_edge("execute_action", "generate_reply")

# 응답 생성 -> 조건부 종료
# action_required가 False면 END로, True면 task_decision으로
builder.add_conditional_edges(
    "generate_reply",
    lambda x: END if not x.get("action_required", False) else "task_decision",
    [END, "task_decision"]
)

# 그래프 컴파일
checkpointer = InMemorySaver()
store = InMemoryStore()
graph = builder.compile(checkpointer, store=store)
