"""LLM을 사용하여 대화 응답을 생성하는 모듈입니다."""
import os
from typing import Dict
from langchain.chat_models import init_chat_model
from langchain.schema import SystemMessage, HumanMessage, AIMessage
from src.state import ChatState


def generate_reply(state: ChatState) -> Dict:
    """현재 상태를 기반으로 응답을 생성합니다.
    
    Args:
        state (ChatState): 현재 대화 상태

    Returns:
        Dict: 업데이트된 상태
    """
    model = init_chat_model(
        os.getenv("DEFAULT_MODEL"),
        temperature=0.7,
        max_tokens=1024,
    )
    # 컨텍스트 구성
    context_parts = [
        f"사용자 입력: {state['user_input']}",
        f"분석된 의도: {state['parsed_intent'].get('intent')}",
        f"추출된 파라미터: {state['parsed_intent'].get('params', {})}"
    ]
    # 실행 결과가 있다면 컨텍스트에 추가
    executed_result = state.get("executed_result", {})
    if executed_result:
        # 도구 실행 결과가 문자열이면 바로 반환
        if isinstance(executed_result.get("details"), str):
            return {
                "reply": executed_result.get("details"),
                "messages": state.get("messages", [])
            }
        # 도구 실행 결과가 dict 등일 때 자연어로 요약
        context_parts.append(f"도구 실행 결과: {executed_result}")
    context = "\n".join(context_parts)
    system_prompt = """
    당신은 친절하고 전문적인 AI 어시스턴트입니다. 
    주어진 컨텍스트와 도구 실행 결과를 바탕으로 적절한 응답을 자연어로 생성해주세요.
    - 일정 관련 작업이 성공했다면, 구체적인 시간과 세부사항을 포함해서 답변해주세요.
    - 작업이 실패했다면, 실패 원인과 가능한 해결 방안을 제시해주세요.
    - 일반 대화의 경우, 자연스럽고 친근한 톤으로 응답해주세요.
    """
    # 이전 대화 히스토리 추가 (최대 3턴)
    history = state["messages"][-6:] if state["messages"] else []
    messages = [
        SystemMessage(content=system_prompt),
        HumanMessage(content=context)
    ]
    messages.extend(history)  # 히스토리 추가
    try:
        response = model.invoke(messages)
        if not response.content:
            raise ValueError("모델 응답이 비어있습니다")
        return {
            "reply": response.content,
            "messages": state["messages"] + [response] if state["messages"] else [response]
        }
    except Exception as e:
        print(f"응답 생성 중 오류 발생: {str(e)}")
        return {
            "reply": "죄송합니다. 응답을 생성하는 중 오류가 발생했습니다.",
            "messages": state["messages"] if state["messages"] else []
        }
