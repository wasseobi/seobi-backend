"""Graph module for General Agent implementation."""
from langgraph.checkpoint.memory import MemorySaver
from langgraph.graph import StateGraph, START, END
from langgraph.prebuilt import ToolNode, tools_condition
from app.utils.openai_client import init_langchain_llm

from .agent_state import State
from .nodes.agent_node import agent_node

memory = MemorySaver()

def mcp_graph(tools):
    """MCP Graph 생성 함수"""
    print("🔧 MCP Tools:", tools)

    # LLM 설정
    llm = init_langchain_llm()

    # 도구 노드 생성 (기본 설정 사용)
    tool_node = ToolNode(tools)

    # 그래프 생성
    workflow = StateGraph(State)
    
    # agent_node를 tools와 함께 호출하는 래퍼 함수
    def agent_node_wrapper(state):
        return agent_node(state, tools)
    
    # 노드 추가
    workflow.add_node("agent", agent_node_wrapper)
    workflow.add_node("tools", tool_node)
    
    # 엣지 추가 - 조건부 구조로 복원
    workflow.add_edge(START, "agent")
    workflow.add_conditional_edges(
        "agent",
        tools_condition,
        {
            "tools": "tools",
            END: END
        }
    )
    workflow.add_edge("tools", "agent")
    
    # 메모리 설정
    app = workflow.compile(checkpointer=memory)
    
    return app