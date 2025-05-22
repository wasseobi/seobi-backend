"""대화 응답을 생성하는 모듈입니다."""
from typing import Dict, Any, List
from langchain.schema import HumanMessage, AIMessage, SystemMessage, FunctionMessage
from app.utils.openai_client import get_completion, get_openai_client
from app.langgraph.tools import get_tools
from app.langgraph.state import ChatState


def get_base_prompt() -> str:
    return """당신은 친절하고 전문적인 AI 어시스턴트입니다.
사용자의 질문이나 이전 도구 실행 결과를 바탕으로 적절한 응답을 생성하세요

지침:
1. 도구 실행 결과가 있다면 그대로 사용하여 자연스러운 대화체로 응답하세요
2. 새로운 도구 호출을 하지 마세요
3. JSON이나 tool_calls 형식으로 응답하지 마세요
4. 단순히 받은 결과를 자연스럽게 변환하여 답변하세요"""


def generate_reply(state: Dict) -> Dict:
    """주어진 상태를 기반으로 응답을 생성합니다."""
    try:
        if isinstance(state, (list, dict)):
            state = ChatState.from_dict(state)
            
        # 컨텍스트 준비
        context_parts = []
        
        # 기본 정보
        context_parts.append(f"사용자 입력: {state.get('user_input', '')}")
        
        # 도구 실행 결과가 있다면 추가
        if state.get("executed_result", {}).get("success") and state.get("executed_result", {}).get("details"):
            context_parts.append(f"도구 실행 결과: {state['executed_result']['details']}")
        elif state.get("executed_result", {}).get("error"):
            context_parts.append(f"도구 실행 실패: {state['executed_result']['error']['message']}")
        
        context = "\n".join(context_parts)
        print(f"[DEBUG][generate_reply] 컨텍스트: {context}")
        
        # 메시지 준비
        messages = [
            {"role": "system", "content": get_base_prompt()},
            {"role": "user", "content": context}
        ]
        print(f"[DEBUG][generate_reply] 전송할 메시지: {messages}")
        
        # 응답 생성
        client = get_openai_client()
        response = get_completion(client, messages)
        print(f"[DEBUG][generate_reply] 모델 응답: {response}")
        
        if not response:
            raise ValueError("모델 응답이 비어있습니다")
        
        # 응답을 상태에 추가하고 action_required를 False로 설정
        result = state.to_dict()
        result["reply"] = response
        result["action_required"] = False  # 응답 생성 후에는 항상 False
        result["messages"] = state.get("messages", []) + [AIMessage(content=response)]
        return result
        
    except Exception as e:
        print(f"[ERROR][generate_reply] 응답 생성 중 오류 발생: {str(e)}")
        result = state.to_dict()
        result["reply"] = f"죄송합니다. 응답을 생성하는 중에 오류가 발생했습니다: {str(e)}"
        result["action_required"] = False
        return result
