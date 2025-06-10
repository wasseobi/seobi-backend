"""General Agent 실행기."""
import asyncio
import dotenv
import os
from typing import List, Dict
from langchain_core.runnables import RunnableConfig
from langchain_openai import ChatOpenAI
from langchain_mcp_adapters.client import MultiServerMCPClient
from langchain_core.messages import HumanMessage, AIMessage, ToolMessage, SystemMessage

from .graph import mcp_graph

dotenv.load_dotenv()

async def general_agent(message: str, conversation_history: List[Dict] = None):
    """메인 함수 - General Agent 실행"""
    config = RunnableConfig(
        recursion_limit=15,  # 도구 호출 횟수 제한을 늘림
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
    
    try:
        tools = await client.get_tools()
        agent = mcp_graph(tools)
        
        # 시스템 프롬프트 추가
        system_message = SystemMessage(content="""당신은 도움이 되는 AI 어시스턴트입니다. 
사용자의 질문에 답변할 때 필요한 도구를 적극적으로 사용하세요.
위치나 장소에 대한 질문이 있으면 Google Maps 도구를 사용하여 정확한 정보를 제공하세요.
항상 한국어로 답변하세요.""")
        
        # 대화 기록이 있으면 함께 전달
        if conversation_history:
            # 대화 기록을 HumanMessage와 AIMessage로 변환
            messages = [system_message]  # 시스템 메시지 먼저 추가
            for msg in conversation_history:
                if msg['role'] == 'user':
                    messages.append(HumanMessage(content=msg['content']))
                elif msg['role'] == 'assistant':
                    messages.append(AIMessage(content=msg['content']))
                # tool 메시지는 건너뛰기 (LangGraph에서 처리)
            
            # 현재 메시지 추가
            messages.append(HumanMessage(content=message))
        else:
            # 대화 기록이 없으면 시스템 메시지와 현재 메시지만
            messages = [system_message, HumanMessage(content=message)]
        
        response = await agent.ainvoke(
            {"messages": messages},  # 올바른 형식으로 전달
            config=config
        )
        print("📨 Agent Response:", response)
        
        # 전체 메시지 히스토리 반환 (도구 사용 정보 포함)
        return response
    except Exception as e:
        print(f"Error in general_agent: {e}")
        raise 