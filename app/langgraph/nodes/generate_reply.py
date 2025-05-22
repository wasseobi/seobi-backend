"""LLM을 사용하여 대화 응답을 생성하는 모듈입니다."""
import os
from typing import Dict
from app.utils.openai_client import get_completion, get_openai_client
from langchain.schema import SystemMessage, HumanMessage, AIMessage
from app.langgraph.state import ChatState


def generate_reply(state: ChatState) -> Dict:
    """현재 상태를 기반으로 응답을 생성합니다.
    
    Args:
        state (ChatState): 현재 대화 상태

    Returns:
        Dict: 업데이트된 상태
    """
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
    system_prompt = '''
    당신은 친절하고 전문적인 AI 어시스턴트입니다.
    아래 도구 목록 중 사용자의 요청에 맞는 도구가 있다면 반드시 tool_calls JSON 형식으로 응답하세요.

    사용 가능한 도구 목록:
    - get_current_time: 현재 시간을 반환합니다.
    - google_search: 구글 검색 결과를 반환합니다.
    - schedule_meeting: 일정을 등록합니다.

    예시:
    {
      "tool_calls": [
        {
          "id": "tool-call-id",
          "type": "function",
          "function": {
            "name": "google_search",
            "arguments": "{\\"query\\": \\\"대전역 위치\\\"}"
          }
        }
      ]
    }
    단순 대화라면 일반 답변만 하세요.
    '''
    # 이전 대화 히스토리 추가 (최대 3턴)
    history = state["messages"][-6:] if state["messages"] else []
    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": context}
    ]
    for msg in history:
        if hasattr(msg, "content"):
            messages.append({"role": "user", "content": msg.content})
    try:
        client = get_openai_client()
        response_content = get_completion(
            client,
            messages=messages,
            max_completion_tokens=1024
        )
        if not response_content:
            raise ValueError("모델 응답이 비어있습니다")
        result = {
            "reply": response_content,
            "messages": state["messages"] + [AIMessage(content=response_content)] if state["messages"] else [AIMessage(content=response_content)]
        }
        if not isinstance(result, dict):
            print("[ERROR] 반환값이 dict가 아님! type:", type(result), "value:", repr(result))
            raise TypeError("노드 반환값은 반드시 dict여야 합니다.")
        return result
    except Exception as e:
        print(f"응답 생성 중 오류 발생: {str(e)}")
        result = {
            "reply": "죄송합니다. 응답을 생성하는 중 오류가 발생했습니다.",
            "messages": state["messages"] if state["messages"] else []
        }
        if not isinstance(result, dict):
            print("[ERROR] 반환값이 dict가 아님! type:", type(result), "value:", repr(result))
            raise TypeError("노드 반환값은 반드시 dict여야 합니다.")
        return result
    print("[DEBUG][generate_reply] reply 필드:", state.get("reply"))
    result = {**state, "reply": state.get("reply")}
    if not isinstance(result, dict):
        print("[ERROR] 반환값이 dict가 아님! type:", type(result), "value:", repr(result))
        raise TypeError("노드 반환값은 반드시 dict여야 합니다.")
    print("[DEBUG][generate_reply] 반환값 type:", type(result))
    print("[DEBUG][generate_reply] 반환값:", result)
    return result
