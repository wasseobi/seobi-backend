"""작업 실행 여부를 결정하는 모듈입니다."""
from typing import Dict
from app.langgraph.state import ChatState
import json

# 실제 등록된 tool 이름만 분기
ACTION_REQUIRED_INTENTS = {"current_time", "google_search", "schedule_meeting"}

def task_decision(state: ChatState) -> Dict:
    print("[DEBUG] task_decision type:", type(task_decision))
    print("[DEBUG][task_decision] 함수 진입, state type:", type(state))
    print("[DEBUG][task_decision] state repr:", repr(state))
    
    parsed_intent = state["parsed_intent"]
    intent = parsed_intent["intent"] if isinstance(parsed_intent, dict) else ""
    params = parsed_intent.get("params", {}) if isinstance(parsed_intent, dict) else {}

    tools = state.get("tools", [])
    print("[DEBUG][task_decision] tools type:", type(tools))
    print("[DEBUG][task_decision] tools:", tools)

    # float 타입 파라미터 방어: num_results 등은 int로 변환
    if "num_results" in params and isinstance(params["num_results"], float):
        print(f"[task_decision] num_results(float) → int 변환: {params['num_results']} → {int(params['num_results'])}")
        params["num_results"] = int(params["num_results"])
        parsed_intent["params"] = params  # 반드시 state에 반영
        state["parsed_intent"] = parsed_intent

    # SystemMessage를 제외한 messages만 출력
    filtered_messages = [m for m in state["messages"] if m.__class__.__name__ != "SystemMessage"]
    print("[DEBUG][task_decision] (SystemMessage 제외) messages:", filtered_messages)

    # reply 파싱 결과에서 intent 추출 시도
    reply = state.get("reply")
    parsed_reply = None
    if reply:
        try:
            parsed_reply = json.loads(reply)
            print("[DEBUG][task_decision] reply 파싱 결과:", parsed_reply)
        except Exception as e:
            print("[DEBUG][task_decision] reply 파싱 에러:", e)

    # intent 추출 로직 개선: tool_calls가 있으면 intent를 tool name으로 설정
    intent = parsed_intent["intent"] if isinstance(parsed_intent, dict) else ""
    params = parsed_intent.get("params", {}) if isinstance(parsed_intent, dict) else {}
    if parsed_reply and "tool_calls" in parsed_reply and parsed_reply["tool_calls"]:
        tool_name = parsed_reply["tool_calls"][0]["function"]["name"]
        print(f"[DEBUG][task_decision] tool_calls에서 intent 추출: {tool_name}")
        intent = tool_name

    print(f"[task_decision] intent: {intent!r}, action_required: {intent in ACTION_REQUIRED_INTENTS}")

    # state["tools"]가 문자열 리스트인지 객체 리스트인지에 따라 분기
    if tools and all(isinstance(t, str) for t in tools):
        tool_intents = set(tools)
    elif tools and all(hasattr(t, "name") for t in tools):
        tool_intents = {t.name for t in tools}
    else:
        tool_intents = {"google_search", "get_current_time", "schedule_meeting"}
    print("[DEBUG][task_decision] tool_intents:", tool_intents)

    action_required = intent in tool_intents and intent != "general_chat"
    print(f"[task_decision] intent: '{intent}', action_required: {action_required}")

    result = {
        **state,
        "action_required": action_required
    }
    if not isinstance(result, dict):
        print("[ERROR] 반환값이 dict가 아님! type:", type(result), "value:", repr(result))
        raise TypeError("노드 반환값은 반드시 dict여야 합니다.")
    return result
