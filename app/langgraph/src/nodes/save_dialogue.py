"""대화 내용을 저장하는 모듈입니다."""
from typing import Dict
import json
import os
from datetime import datetime

from src.state import ChatState


def save_dialogue(state: ChatState) -> Dict:
    """대화 내용을 저장소에 기록합니다.
    
    Args:
        state (ChatState): 현재 대화 상태

    Returns:
        Dict: 업데이트된 상태
    """    # 저장할 대화 데이터 구성
    dialogue_data = {
        "timestamp": state["timestamp"],
        "user_id": state["user_id"],
        "user_input": state["user_input"],
        "parsed_intent": state["parsed_intent"] if isinstance(state["parsed_intent"], dict) else {},
        "system_reply": state.get("reply", ""),
        "action_required": state.get("action_required", False),
        "executed_result": state.get("executed_result", {}),
        "messages": [msg.dict() if hasattr(msg, 'dict') else msg for msg in state.get("messages", [])] if state.get("messages") else []
    }
    
    try:
        # 대화 저장 디렉토리 생성
        save_dir = os.path.join(os.path.dirname(__file__), "..", "..", "data", "dialogues")
        os.makedirs(save_dir, exist_ok=True)
        
        # 대화 ID 생성 (timestamp + user_id)
        dialogue_id = f"{datetime.now().strftime('%Y%m%d_%H%M%S')}_{state['user_id']}"
        
        # 파일에 저장
        file_path = os.path.join(save_dir, f"{dialogue_id}.json")
        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(dialogue_data, f, ensure_ascii=False, indent=2)
            
        print(f"💾 대화 저장됨: {file_path}")
        
    except Exception as e:
        print(f"⚠️ 대화 저장 실패: {str(e)}")
        # 저장 실패해도 대화는 계속 진행
    
    return state
