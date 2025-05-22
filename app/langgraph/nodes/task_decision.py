"""작업 실행 여부를 결정하는 모듈입니다."""
from typing import Dict
from app.langgraph.state import ChatState
import json

# 실제 등록된 tool 이름만 분기
ACTION_REQUIRED_INTENTS = {"get_current_time", "google_search", "schedule_meeting"}

def task_decision(state: ChatState) -> Dict:
    # state가 list나 dict로 들어올 수 있으므로 ChatState로 변환
    if isinstance(state, (list, dict)):
        state = ChatState.from_dict(state)
    
    parsed_intent = state["parsed_intent"]
    intent = parsed_intent["intent"] if isinstance(parsed_intent, dict) else ""
    params = parsed_intent.get("params", {}) if isinstance(parsed_intent, dict) else {}

    # float 타입 파라미터 방어: num_results 등은 int로 변환
    if "num_results" in params and isinstance(params["num_results"], float):
        params["num_results"] = int(params["num_results"])
        parsed_intent["params"] = params
        state["parsed_intent"] = parsed_intent

    executed_result = state.get("executed_result", {})
    if executed_result and executed_result.get("success"):
        action_required = False
    else:
        # general_chat이거나 등록된 도구가 아닌 경우 action_required를 False로 설정
        action_required = intent != "general_chat" and intent in ACTION_REQUIRED_INTENTS

    result = state.to_dict()
    result["action_required"] = action_required
    return result
