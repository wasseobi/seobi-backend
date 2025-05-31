from app.langgraph.agent.agent_state import AgentState
from app.utils.openai_client import get_openai_client, get_completion
from langchain_core.messages import BaseMessage
from typing import List

def summarize_node(state: AgentState) -> AgentState:
    MAX_MESSAGES = 6
    messages: List[BaseMessage] = state["messages"]
    if len(messages) > MAX_MESSAGES:
        # 최근 메시지 텍스트만 추출
        to_summarize = messages[:-2]
        prompt = "다음 대화 내용을 한글로 간결하게 요약해줘.\n" + "\n".join([m.content for m in to_summarize])
        client = get_openai_client()
        llm_messages = [
            {"role": "system", "content": "아래 대화 내용을 요약해줘."},
            {"role": "user", "content": prompt}
        ]
        summary = get_completion(client, llm_messages)
        # 최근 2개 메시지만 남기고 나머지는 요약
        new_messages = messages[-2:]
        return {
            **state,
            "summary": summary,
            "messages": new_messages
        }
    else:
        return state
