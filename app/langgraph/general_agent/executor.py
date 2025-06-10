"""General Agent 실행기 (MCP + 직접 구현 도구 통합)."""
import asyncio
import dotenv
import os
from typing import List, Dict
from langchain_core.runnables import RunnableConfig
from langchain_openai import ChatOpenAI
from langchain_mcp_adapters.client import MultiServerMCPClient
from langchain_core.messages import HumanMessage, AIMessage, ToolMessage, SystemMessage

from .graph import mcp_graph
from .agent_state import AgentState
from ..tools import agent_tools

dotenv.load_dotenv()

async def general_agent(message: str, conversation_history: List[Dict] = None, user_id: str = None):
    """메인 함수 - General Agent 실행 (MCP + 직접 구현 도구 통합)"""
    config = RunnableConfig(
        recursion_limit=25,  # 재귀 한계 증가
        configurable={"thread_id": "1"},
        tags=["my-tag"]
    )

    # 새로운 방식으로 MCP 클라이언트 사용
    client = MultiServerMCPClient(
        {
            "googlemap": {
                "url": os.getenv("GOOGLE_MAP_MCP_URL"),
                "transport": "streamable_http",
            }
        }
    )

    # MCP 도구 가져오기
    mcp_tools = []
    try:
        # 올바른 메서드 사용
        mcp_tools = await client.get_tools()
        print(f"🔧 MCP Tools loaded: {len(mcp_tools)} tools")
        print(f"🔧 MCP Tool names: {[tool.name for tool in mcp_tools]}")
    except Exception as e:
        print(f"⚠️ MCP Tools loading failed: {e}")
        mcp_tools = []

    # 통합된 그래프 생성
    agent = mcp_graph(mcp_tools)

    # 메시지 초기화
    messages = []
    
    # 대화 기록 추가
    if conversation_history:
        for msg in conversation_history:
            if msg.get('role') == 'user':
                messages.append(HumanMessage(content=msg.get('content', '')))
            elif msg.get('role') == 'assistant':
                messages.append(AIMessage(content=msg.get('content', '')))

    # 현재 메시지 추가
    messages.append(HumanMessage(content=message))

    # AgentState 초기화
    state = AgentState(
        messages=messages,
        user_id=user_id,
        user_location=None,  # 필요시 위치 정보 추가
        current_input=message
    )
    
    # 도구 설정 (MCP + 직접 구현)
    state.set_tools(mcp_tools=mcp_tools, direct_tools=agent_tools)
    
    print(f"🔧 Total tools available: {len(state.get_all_tools())}")
    print(f"🔧 MCP tools: {len(mcp_tools)}")
    print(f"🔧 Direct tools: {len(agent_tools)}")
    print(f"🔧 Direct tool names: {[tool.name for tool in agent_tools]}")
    print(f"🔧 All tool names: {[tool.name for tool in state.get_all_tools()]}")
    
    # 메시지 전달 확인
    print(f"📨 Messages to send: {len(messages)}")
    print(f"📨 Message contents: {[msg.content for msg in messages]}")
    print(f"📨 State messages: {len(state.messages)}")
    
    state_dict = state.to_dict()
    print(f"📨 State dict messages: {len(state_dict.get('messages', []))}")

    try:
        # Agent 실행
        response = await agent.ainvoke(
            state_dict,  # dict 형태로 변환하여 전달
            config=config
        )
        print("📨 Agent Response:", response)
        
        # 응답이 dict 형태로 반환되므로 그대로 반환
        return response
        
    except Exception as e:
        print(f"❌ Error in general_agent: {e}")
        # 오류 발생 시 기본 응답 반환
        error_state = AgentState(
            messages=messages + [AIMessage(content=f"죄송합니다. 오류가 발생했습니다: {str(e)}")],
            user_id=user_id,
            current_input=message
        )
        return error_state.to_dict()
    
    finally:
        # MCP 클라이언트 정리
        try:
            await client.aclose()
        except:
            pass 