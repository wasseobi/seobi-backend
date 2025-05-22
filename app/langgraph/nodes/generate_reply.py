"""현재까지의 대화 컨텍스트를 바탕으로 응답을 생성하는 모듈입니다."""
from typing import Dict, List
from langchain.schema import HumanMessage, AIMessage, BaseMessage
from app.utils.openai_client import get_completion, get_openai_client
from app.langgraph.state import ChatState


def create_openai_messages(state_messages: List[BaseMessage]) -> List[Dict[str, str]]:
    """주어진 메시지 리스트를 OpenAI 메시지 형식으로 변환합니다."""
    openai_messages = []
    for msg in state_messages:
        role = "user" if isinstance(msg, HumanMessage) else "assistant"
        openai_messages.append({"role": role, "content": msg.content})
    return openai_messages


def generate_reply(state: Dict) -> Dict:
    """현재까지의 대화 컨텍스트를 바탕으로 응답을 생성합니다."""
    try:
        if isinstance(state, (list, dict)):
            state = ChatState.from_dict(state)

        # 이전 컨텍스트에서 메시지 가져오기
        context = state.get("messages", [])
        if not context:
            return state.to_dict()

        # OpenAI 메시지 형식으로 변환
        messages = create_openai_messages(context)

        client = get_openai_client()
        response = get_completion(client, messages)

        if not response:
            raise ValueError("Empty response from model")

        # 응답을 메시지에 추가
        messages = state.get("messages", [])
        messages.append(AIMessage(content=response))

        # 완료된 상태 반환
        completed_state = {
            **state.to_dict(),
            "messages": messages,
            "action_required": False
        }

        return completed_state

    except Exception as e:
        # 오류 발생 시 현재 상태 유지
        error_message = AIMessage(content=f"응답 생성 중 오류가 발생했습니다: {str(e)}")
        messages = state.get("messages", [])
        messages.append(error_message)
        return {**state.to_dict(), "messages": messages}
