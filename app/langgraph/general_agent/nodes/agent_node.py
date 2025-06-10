"""Agent node for general agent."""
from typing import Dict, Any, List
from langchain_core.messages import HumanMessage, AIMessage, ToolMessage, SystemMessage
from app.utils.openai_client import init_langchain_llm

def agent_node(state: Dict[str, Any], tools: List = None) -> Dict[str, Any]:
    """LLM 노드 - 상태에서 메시지를 가져와서 처리"""
    # LLM 설정
    llm = init_langchain_llm()
    
    # 도구 호출 횟수 제한을 위한 설정
    if tools:
        llm_with_tools = llm.bind_tools(tools)
    else:
        llm_with_tools = llm
    
    return {"messages": [llm_with_tools.invoke(state["messages"])]} 