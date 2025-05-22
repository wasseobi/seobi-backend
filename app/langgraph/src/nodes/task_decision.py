"""작업 실행 여부를 결정하는 모듈입니다."""
from typing import Dict
from src.state import ChatState

# 실제 등록된 tool 이름만 분기
ACTION_REQUIRED_INTENTS = {"current_time", "google_search", "schedule_meeting"}

def task_decision(state: ChatState) -> Dict:
    """현재 의도에 따라 추가 작업 필요 여부를 결정합니다.
    Args:
        state (ChatState): 현재 대화 상태
    Returns:
        Dict: 업데이트된 상태
    """
    parsed_intent = state["parsed_intent"]
    intent = parsed_intent["intent"] if isinstance(parsed_intent, dict) else ""
    params = parsed_intent.get("params", {}) if isinstance(parsed_intent, dict) else {}

    # float 타입 파라미터 방어: num_results 등은 int로 변환
    if "num_results" in params and isinstance(params["num_results"], float):
        print(f"[task_decision] num_results(float) → int 변환: {params['num_results']} → {int(params['num_results'])}")
        params["num_results"] = int(params["num_results"])
        parsed_intent["params"] = params  # 반드시 state에 반영
        state["parsed_intent"] = parsed_intent

    print(f"[task_decision] intent: {intent!r}, action_required: {intent in ACTION_REQUIRED_INTENTS}")

    if intent in ACTION_REQUIRED_INTENTS:
        print(f"[task_decision] action_required: True (intent: {intent})")
        return {
            "action_required": True,
            "tool_info": {
                "name": intent,
                "input": params
            }
        }
    print(f"[task_decision] action_required: False (intent: {intent})")
    # 작업이 필요없는 경우
    return {
        "action_required": False,
        "tool_info": None
    }
