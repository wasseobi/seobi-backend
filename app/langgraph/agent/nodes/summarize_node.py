from app.langgraph.agent.agent_state import AgentState
from app.utils.openai_client import get_openai_client, get_completion
from langchain_core.messages import BaseMessage, HumanMessage, RemoveMessage
from typing import Dict


def delete_message(state: AgentState) -> Dict:
    messages = state.get("messages")
    if len(messages) > 3:
        return {"messages": [RemoveMessage(id=m.id) for m in messages[:-3]]}


def summarize_node(state: AgentState) -> AgentState:
    try:
        summary = state.get("summary", "")
        if summary:
            summary_message = (f"이것은 이전 대화의 요약입니다. : \n{summary}\n"
                               "아래 새로운 메세지와 함께 새로운 요약을 작성해주세요.")
        else:
            summary_message = "한글로 아래 메세지의 요약을 작성해주세요."
        summarize_message = [HumanMessage(
            content=summary_message)] + state["messages"]

        response = get_completion(get_openai_client(), summarize_message)
        state["summary"] = response.content.strip()
        message_update = delete_message(state)
        state["messages"] = message_update["messages"]
        state["next_step"] = "end"

    except Exception as e:
        state["next_step"] = "end"

    return state
