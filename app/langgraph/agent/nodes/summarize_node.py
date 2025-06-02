from app.langgraph.agent.agent_state import AgentState
from app.utils.openai_client import get_openai_client, get_completion
from langchain_core.messages import BaseMessage, HumanMessage, RemoveMessage
import logging
from typing import Dict, List, Union

# summarize 로거 설정
log = logging.getLogger("langgraph_debug")


def delete_message(state: AgentState) -> List[BaseMessage]:
    """오래된 메시지를 제거하고 새로운 메시지 리스트를 반환합니다."""
    messages = getattr(state, "messages", [])
    if len(messages) > 3:
        # 마지막 3개 메시지만 유지
        return messages[-3:]
    return messages


def summarize_node(state: AgentState) -> AgentState:
    """대화 내용을 요약하고 오래된 메시지를 정리하는 노드."""
    try:
        log.info("[Summarize] Starting summarization...")

        # 기존 요약 확인
        summary = getattr(state, "summary", "")
        if not hasattr(state, "messages"):
            state.messages = []

        # 요약 프롬프트 구성
        if summary:
            summary_message = (f"이것은 이전 대화의 요약입니다. : \n{summary}\n"
                               "아래 새로운 메세지와 함께 새로운 요약을 작성해주세요.")
        else:
            summary_message = "한글로 아래 메세지의 요약을 작성해주세요."

        # 메시지 배열 구성
        summarize_message = [HumanMessage(
            content=summary_message), *state.messages]

        # 요약 생성
        response = get_completion(get_openai_client(), summarize_message)
        state.summary = response.content.strip()
        log.info(f"[Summarize] Generated summary: {state.summary}")

        # 메시지 정리
        state.messages = delete_message(state)
        log.info(
            f"[Summarize] Cleaned messages, remaining count: {len(state.messages)}")

        # 다음 단계 설정
        state.next_step = "end"

    except Exception as e:
        log.error(f"[Summarize] Error during summarization:", exc_info=True)
        state.error = str(e)
        state.next_step = "end"

    return state
