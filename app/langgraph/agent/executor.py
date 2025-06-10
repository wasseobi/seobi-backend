"""Agent 실행기 생성."""
from typing import Dict, List, Callable, Any
from langchain_core.messages import BaseMessage, HumanMessage, AIMessage
from .agent_state import AgentState

from .graph import build_graph

from langchain_mcp_adapters.client import MultiServerMCPClient
from langchain_core.runnables import RunnableConfig
import dotenv
import os

dotenv.load_dotenv()

async def create_agent_executor() -> Callable:
    """Agent 실행기를 생성합니다."""
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
        mcp_tools = await client.get_tools()
        print(f"🔧 MCP Tools loaded: {len(mcp_tools)} tools")
        print(f"🔧 MCP Tool names: {[tool.name for tool in mcp_tools]}")
    except Exception as e:
        print(f"⚠️ MCP Tools loading failed: {e}")
        mcp_tools = []
    
    graph = build_graph(mcp_tools)
    compiled_graph = graph.compile()
    
    async def invoke(
        input_text: str,
        chat_history: List[BaseMessage] = None
    ) -> Dict[str, Any]:
        """입력된 텍스트로 그래프를 실행합니다."""
        if chat_history is None:
            chat_history = []
            
        # 초기 상태 설정 (사용자 입력을 한 번만 추가)
        state = AgentState(
            messages=[],  # 빈 리스트로 시작
            current_input=input_text,  # 현재 입력만 저장
            scratchpad=[],
            step_count=0,
            next_step="agent"
        )
        
        try:
            # 그래프 실행
            result = await compiled_graph.ainvoke(state, config=config)
            
            if isinstance(result, dict) and "messages" in result:
                return result
            return state
            
        except Exception as e:
            print(f"❌ Error in invoke: {e}")
            import traceback
            traceback.print_exc()
            state["messages"] = [AIMessage(content="죄송합니다. 처리 중 오류가 발생했습니다.")]
            return state
        finally:
            # MCP 클라이언트 정리
            try:
                await client.aclose()
            except:
                pass 
    return invoke
