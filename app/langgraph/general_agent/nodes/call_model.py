"""LLM 호출 및 응답 생성 모듈 (MCP + 직접 구현 도구 통합)."""
import json
import logging
import os
from typing import Dict, List, Any, Union
from langchain_core.messages import AIMessage, ToolMessage, BaseMessage, HumanMessage, SystemMessage
from datetime import datetime

from app.utils.openai_client import init_langchain_llm
from app.utils.message.converter import convert_to_openai_messages
from app.utils.message.formatter import format_message_content, format_message_list
from ...tools import agent_tools
from ..agent_state import AgentState
from ....utils.prompt.agent_prompt import prompt

# 로그 디렉토리 설정
LOG_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))), 'logs')
os.makedirs(LOG_DIR, exist_ok=True)  # logs 폴더가 없으면 생성
LOG_PATH = os.path.join(LOG_DIR, 'langgraph_debug.log')

# 로거 설정
log = logging.getLogger(__name__)

def format_tool_results(tool_results: List[Any]) -> Dict:
    """도구 실행 결과를 ToolMessage 형식으로 변환."""
    
    if not tool_results:
        log.warning("[CallModel:format_tool_results] Empty tool_results")
        return None
        
    # 도구 실행 결과를 구조화
    formatted_output = {
        "stdout": "",
        "artifacts": [],
        "status": "success"
    }

    try:
        # 결과가 단일 값인 경우 리스트로 변환
        if not isinstance(tool_results, list):
            tool_results = [tool_results]

        for result in tool_results:
            
            if isinstance(result, dict):
                # 결과가 dict인 경우 artifact로 저장
                formatted_output["artifacts"].append(result)
                if "content" in result:
                    formatted_output["stdout"] += str(result["content"]) + "\n"
            else:
                # 단순 문자열인 경우 stdout으로 처리
                formatted_output["stdout"] += str(result) + "\n"
                
        return formatted_output
            
    except Exception as e:
        log.error(f"[CallModel:format_tool_results] Error formatting tool results: {str(e)}", exc_info=True)
        formatted_output["status"] = "error"
        formatted_output["stdout"] = f"Error formatting tool results: {str(e)}"
        return formatted_output

def call_model(state: Union[Dict, AgentState]) -> Union[Dict, AgentState]:
    """LLM을 호출하고 응답을 생성하는 노드 (MCP + 직접 구현 도구 통합)."""
    try:
        # state가 dict인지 AgentState인지 확인
        is_dict = isinstance(state, dict)
        
        # 기본 state 구조 확인 및 초기화
        if is_dict:
            messages = state["messages"]
            user_location = state.get("user_location")
            summary = state.get("summary")
            user_id = state.get("user_id")
            user_memory = state.get("user_memory", "")
            # 모든 도구 가져오기 (MCP + 직접 구현)
            all_tools = []
            if state.get("mcp_tools"):
                all_tools.extend(state["mcp_tools"])
            if state.get("direct_tools"):
                all_tools.extend(state["direct_tools"])
            if not all_tools:
                all_tools = agent_tools  # 기본 도구
        else:
            messages = state.messages
            user_location = state.user_location
            summary = state.summary
            user_id = state.user_id
            user_memory = state.user_memory or ""
            # 모든 도구 가져오기 (MCP + 직접 구현)
            all_tools = state.get_all_tools()
            if not all_tools:
                all_tools = agent_tools  # 기본 도구

        # 메시지 검증
        if not messages:
            log.error("[CallModel] No messages in state")
            if is_dict:
                state["next_step"] = "cleanup"
            else:
                state.next_step = "cleanup"
            return state

        # 도구가 바인딩된 모델 초기화
        model = init_langchain_llm(all_tools)
        
        # 도구 목록 로깅
        print(f"🔧 Available tools in call_model: {[tool.name for tool in all_tools]}")
        print(f"🔧 Total tools count: {len(all_tools)}")
        print(f"📨 Processing message: {messages[-1].content if messages else 'No message'}")

        search_results = []
        # 검색 결과를 임시로 비활성화하여 이전 대화 간섭 방지
        # if messages and user_id:
        #     from app.services.message_service import MessageService
        #     message_service = MessageService()
        #     latest_message = messages[-1].content if messages else ""
        #     
        #     # 현재 질문과 관련된 검색만 수행
        #     search_results = message_service.search_similar_messages_pgvector(
        #         user_id=str(user_id),
        #         query=latest_message,
        #         top_k=3
        #     )
        #     
        #     # 검색 결과 필터링 - 현재 질문과 너무 다른 결과는 제외
        #     filtered_results = []
        #     for result in search_results:
        #         # 검색 결과의 내용이 현재 질문과 유사한지 확인
        #         if result.get('content') and latest_message:
        #             # 간단한 키워드 매칭으로 필터링
        #             current_keywords = set(latest_message.split())
        #             result_keywords = set(result['content'].split())
        #             common_keywords = current_keywords.intersection(result_keywords)
        #             
        #             # 공통 키워드가 있거나 현재 질문이 위치/교통 관련이면 포함
        #             if (len(common_keywords) > 0 or 
        #                 any(keyword in latest_message for keyword in ['역', '지하철', '버스', '길', '위치', '어디', '가다', '오다'])):
        #                 filtered_results.append(result)
        #         
        #     search_results = filtered_results
        #     print(f"🔍 Search results: {len(search_results)} relevant results found")
        
        print("🔍 Search results disabled to prevent interference")

        # 이전 도구 실행 결과 처리
        tool_results = state.get("tool_results") if is_dict else getattr(state, "tool_results", None)
        
        if tool_results:
            tool_output = format_tool_results(tool_results)
            
            if tool_output:
                current_tool_call_id = state.get("current_tool_call_id") if is_dict else getattr(state, "current_tool_call_id", None)
                current_tool_name = state.get("current_tool_name") if is_dict else getattr(state, "current_tool_name", None)
                
                if current_tool_call_id and current_tool_name:
                    tool_message = ToolMessage(
                        content=tool_output["stdout"],
                        tool_call_id=current_tool_call_id,
                        name=current_tool_name
                    )
                    messages.append(tool_message)
                else:
                    log.warning("[CallModel] Missing tool_call_id or tool_name, cannot create ToolMessage")
            else:
                log.warning("[CallModel] Tool output is empty or invalid")
              # 도구 관련 상태 초기화
            if is_dict:
                state["tool_results"] = None
                state["current_tool_call_id"] = None
                state["current_tool_name"] = None
            else:
                state.clear_tool_state()
            
        current_date = datetime.now().strftime("%Y년 %m월 %d일")
        
        # 도구 사용을 유도하는 시스템 메시지 추가
        system_message = SystemMessage(content=f"""당신은 도움이 되는 AI 어시스턴트입니다. 

사용 가능한 도구들:
{chr(10).join([f"- {tool.name}: {tool.description}" for tool in all_tools])}

사용자의 질문에 답변할 때 필요한 도구를 적극적으로 사용하세요:
- 날씨 정보가 필요하면 weather_daily_forecast 도구를 사용하세요
- 위치나 장소에 대한 질문이 있으면 Google Maps 관련 도구를 사용하세요
- 웹 검색이 필요하면 search_web 도구를 사용하세요
- 일정 관리가 필요하면 schedule 관련 도구를 사용하세요

**중요**: 
- 항상 사용자의 현재 질문에만 답변하세요
- 이전 대화 기록은 참고용이므로, 현재 질문과 직접 관련이 없으면 무시하세요
- 검색된 이전 대화 내용이 현재 질문과 다르면 현재 질문에 집중하세요

항상 한국어로 답변하고, 도구를 사용할 때는 정확한 인자를 제공하세요.""")

        # 시스템 메시지를 맨 앞에 추가
        all_messages = [system_message] + messages
        
        # LLM에 전달할 메시지 포맷팅
        formatted_messages = prompt.format_messages(
            messages=all_messages,
            user_location=user_location or "위치 정보 없음",
            current_date=current_date,
            summary=summary or "이전 대화 요약 없음",
            search_results=json.dumps(search_results, ensure_ascii=False) if search_results else "관련 대화 검색 결과 없음",
            user_memory=user_memory or "장기기억 없음"
        )
        
        # OpenAI 형식으로 메시지 변환
        openai_messages = convert_to_openai_messages(formatted_messages)
        
        try:
            # LangChain 모델 호출
            response = model.invoke(openai_messages)
            
            # tool_calls 확인 및 처리
            has_tool_calls = (
                hasattr(response, "additional_kwargs") and 
                "tool_calls" in response.additional_kwargs and
                response.additional_kwargs["tool_calls"]
            )
            
            # 상태 업데이트
            if has_tool_calls:
                tool_calls = response.additional_kwargs["tool_calls"]
                
                if is_dict:
                    state["next_step"] = "tool"
                    # tool 정보 설정
                    state["current_tool_call_id"] = tool_calls[0]["id"]
                    state["current_tool_name"] = tool_calls[0]["function"]["name"]
                    state["current_tool_args"] = tool_calls[0]["function"]["arguments"]
                else:
                    state.next_step = "tool"
                    # tool 정보 설정
                    state.set_tool_info(tool_calls)
                print(f"🔧 Tool call detected: {tool_calls[0]['function']['name']}")
            else:
                # 도구 호출이 없으면 cleanup으로 이동
                if is_dict:
                    state["next_step"] = "cleanup"
                else:
                    state.next_step = "cleanup"
                print("✅ No tool calls - moving to cleanup")
            
            # AI 응답을 messages에 추가
            messages.append(response)
            
            if is_dict:
                state["step_count"] = state.get("step_count", 0) + 1
            else:
                state.step_count += 1
                
            print(f"🤖 AI Response: {response.content}")
            print(f"📊 Step count: {state.get('step_count', 0) if is_dict else state.step_count}")
            
            # 메시지 유효성 검사 (AgentState인 경우에만)
            if not is_dict and not state.validate_messages():
                log.error("[CallModel] Invalid message pattern after adding AI response")
                state.next_step = "cleanup"
                return state
            
        except Exception as e:
            log.error(f"[CallModel] Exception in LLM/tool: {e}", exc_info=True)
            error_msg = AIMessage(content=f"죄송합니다. 응답 생성 중 오류가 발생했습니다: {str(e)}")
            messages.append(error_msg)
            
            if is_dict:
                state["next_step"] = "cleanup"
            else:
                state.next_step = "cleanup"
            return state
            
    except Exception as e:
        log.error(f"[CallModel] Outer exception:", exc_info=True)
        
        # state 타입 다시 확인
        is_dict = isinstance(state, dict)
        
        if is_dict:
            state["error"] = str(e)
            state["next_step"] = "end"
        else:
            state.error = str(e)
            state.next_step = "end"
            
        return state

    return state 