from app.langgraph.agent.agent_state import AgentState
from app.utils.openai_client import get_completion
from langchain_core.messages import BaseMessage, HumanMessage, RemoveMessage, AIMessage
import logging
from typing import Dict, List, Union

# summarize 로거 설정
log = logging.getLogger(__name__)


def delete_message(state: Union[Dict, AgentState]) -> List[BaseMessage]:
    """오래된 메시지를 제거하고 새로운 메시지 리스트를 반환합니다."""
    if isinstance(state, dict):
        messages = state.get("messages", [])
    else:
        messages = getattr(state, "messages", [])

    if len(messages) > 6:
        # 마지막 6개 메시지만 유지
        return messages[-6:]
    return messages


def summarize_node(state: Union[Dict, AgentState]) -> Union[Dict, AgentState]:
    """대화 내용을 요약하고 오래된 메시지를 정리하는 노드."""
    try:
        # state 타입에 따른 처리
        is_dict = isinstance(state, dict)

        # 기존 요약 확인
        if is_dict:
            summary = state.get("summary", "")
            messages = state.get("messages", [])
        else:
            summary = getattr(state, "summary", "")
            messages = getattr(state, "messages", [])

        messages_to_summarize = messages[:-6] if len(messages) > 6 else []
        messages_content = "\n".join([
            f"{'사용자' if isinstance(msg, HumanMessage) else 'AI'}: {msg.content}" 
            for msg in messages_to_summarize
        ])

        # OpenAI 메시지 포맷으로 직접 구성
        summarize_messages = [
            {
                "role": "system",
                "content": "아래 메세지들의 요약을 작성해주세요. 중요한 정보나 의사결정 사항을 포함하고, 300자 이내로 작성해주세요."
            },
            {
                "role": "user",
                "content": f"{summary}\n\n{messages_content}" if summary else messages_content
            }
        ]

        # 요약 생성
        response = get_completion(summarize_messages)
        new_summary = response.strip()

        # 상태 업데이트
        if is_dict:
            state["summary"] = new_summary
            state["messages"] = delete_message(state)
            state["step_count"] = 0
            state["next_step"] = "end"
        else:
            state.summary = new_summary
            state.messages = delete_message(state)
            state.step_count = 0
            state.next_step = "end"

    except Exception as e:
        log.error(
            f"[Summarize] Error during summarization: {str(e)}", exc_info=True)
        if is_dict:
            state["error"] = str(e)
            state["next_step"] = "end"
        else:
            state.error = str(e)
            state.next_step = "end"

    return state
