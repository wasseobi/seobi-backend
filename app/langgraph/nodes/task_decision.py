"""사용자의 의도에 따라 도구 실행 여부를 결정하는 모듈입니다."""
from typing import Dict
from app.langgraph.state import ChatState

def task_decision(state: Dict) -> Dict:
    """사용자의 의도에 따라 도구 실행 여부를 결정합니다."""
    try:
        # ChatState로 변환
        if isinstance(state, dict):
            state = ChatState.from_dict(state)
        
        # parsed_intent에서 의도 추출
        parsed_intent = state.get("parsed_intent", {})
        print(f"[DEBUG][task_decision] 전체 상태: {state.to_dict()}")
        print(f"[DEBUG][task_decision] 파싱된 의도: {parsed_intent}")
        
        # 의도 확인 및 도구 실행 여부 결정
        intent = parsed_intent.get("intent") if isinstance(parsed_intent, dict) else None
        action_required = intent not in [None, "", "general_chat"]
        
        print(f"[DEBUG][task_decision] 도구 실행 필요: {action_required} (의도: {intent})")
        
        # 상태 업데이트 및 반환
        result = state.to_dict()
        result["action_required"] = action_required
        return result
        
    except Exception as e:
        print(f"[ERROR][task_decision] 오류 발생: {str(e)}")
        if isinstance(state, (dict, ChatState)):
            result = state.to_dict() if isinstance(state, ChatState) else state.copy()
            result["action_required"] = False
            return result
        return {
            "action_required": False,
            "parsed_intent": {},
            "messages": []
        }
