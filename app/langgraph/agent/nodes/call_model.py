"""LLM 호출 및 응답 생성 모듈."""
import json
import logging
import os
import pytz
from typing import Dict, List, Any, Union
from langchain_core.messages import AIMessage, ToolMessage, BaseMessage, HumanMessage
from langchain_core.tools import BaseTool
from datetime import datetime

from app.utils.openai_client import init_langchain_llm
from app.utils.message.converter import convert_to_openai_messages
from app.utils.message.formatter import format_message_content, format_message_list
from app.services.user_service import UserService
from ...tools import agent_tools
from ..agent_state import AgentState
from ....utils.prompt.agent_prompt import prompt

# 도구가 바인딩된 모델 초기화
global_model = init_langchain_llm(agent_tools)

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

def call_model(state: Union[Dict, AgentState], mcp_tools: List[BaseTool]) -> Union[Dict, AgentState]:
    """LLM을 호출하고 응답을 생성하는 노드."""
    user_service = UserService()
    try:
        # state가 dict인지 AgentState인지 확인
        is_dict = isinstance(state, dict)
        user = user_service.get_user_by_id(
            state["user_id"] if is_dict else state.user_id)
        user_name = user["username"] if user else None
        # 기본 state 구조 확인 및 초기화
        if is_dict:
            messages = state["messages"]
            user_location = state.get("user_location")
            summary = state.get("summary")
            user_id = state.get("user_id")
            user_memory = state.get("user_memory", "")
        else:
            messages = state.messages
            user_location = state.user_location
            summary = state.summary
            user_id = state.user_id
            user_memory = state.user_memory or ""

        search_results = []
        if messages and user_id:
            from app.services.message_service import MessageService
            message_service = MessageService()
            latest_message = messages[-1].content if messages else ""
            search_results = message_service.search_similar_messages_pgvector(
                user_id=str(user_id),
                query=latest_message,
                top_k=3
            )

        # 이전 도구 실행 결과 처리
        tool_results = state.get("tool_results") if is_dict else getattr(state, "tool_results", None)
        
        # tool_results가 있지만 이미 ToolMessage가 추가되었는지 확인
        if tool_results:
            current_tool_call_id = state.get("current_tool_call_id") if is_dict else getattr(state, "current_tool_call_id", None)
            
            # 이미 해당 tool_call_id에 대한 ToolMessage가 있는지 확인
            tool_message_exists = any(
                isinstance(msg, ToolMessage) and hasattr(msg, "tool_call_id") and msg.tool_call_id == current_tool_call_id
                for msg in messages
            )
            
            if not tool_message_exists:
                # ToolMessage가 없을 때만 추가 (tool_node에서 추가하지 않은 경우)
                tool_output = format_tool_results(tool_results)
                
                if tool_output:
                    current_tool_name = state.get("current_tool_name") if is_dict else getattr(state, "current_tool_name", None)
                    
                    if current_tool_call_id and current_tool_name:
                        tool_message = ToolMessage(
                            content=tool_output["stdout"],
                            tool_call_id=current_tool_call_id,
                            name=current_tool_name
                        )
                        messages.append(tool_message)
                        print(f"[CallModel] Added ToolMessage for {current_tool_name}")
                    else:
                        log.warning("[CallModel] Missing tool_call_id or tool_name, cannot create ToolMessage")
                else:
                    log.warning("[CallModel] Tool output is empty or invalid")
            else:
                print(f"[CallModel] ToolMessage already exists for {current_tool_call_id}")
            
            # 도구 관련 상태 초기화
            if is_dict:
                state["tool_results"] = None
                state["current_tool_call_id"] = None
                state["current_tool_name"] = None
            else:
                state.clear_tool_state()
            
        current_date = datetime.now(pytz.timezone('Asia/Seoul')).strftime("%Y년 %m월 %d일")
        # LLM에 전달할 메시지 포맷팅
        formatted_messages = prompt.format_messages(
            messages=messages,
            user_name=user_name,
            user_location=user_location or "위치 정보 없음",
            current_date=current_date,
            summary=summary or "이전 대화 요약 없음",
            search_results=json.dumps(search_results, ensure_ascii=False) if search_results else "관련 대화 검색 결과 없음",
            user_memory=user_memory or "장기기억 없음"
        )
        
        # OpenAI 형식으로 메시지 변환
        openai_messages = convert_to_openai_messages(formatted_messages)
        
        try:
            # 전역 변수와 충돌하지 않도록 다른 변수명 사용
            bound_llm = global_model.bind_tools(mcp_tools + agent_tools)
            # LangChain 모델 호출
            response = bound_llm.invoke(openai_messages)
            
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
            else:
                if is_dict:
                    state["next_step"] = "end"
                else:
                    state.next_step = "end"
            
            # AI 응답을 messages에 추가
            messages.append(response)
            
            if is_dict:
                state["step_count"] = state.get("step_count", 0) + 1
            else:
                state.step_count += 1
                
            
            # 메시지 유효성 검사 (AgentState인 경우에만)
            if not is_dict and not state.validate_messages():
                log.error("[CallModel] Invalid message pattern after adding AI response")
                state.next_step = "end"
                return state
            
        except Exception as e:
            log.error(f"[CallModel] Exception in LLM/tool: {e}", exc_info=True)
            error_msg = AIMessage(content=f"죄송합니다. 응답 생성 중 오류가 발생했습니다: {str(e)}")
            messages.append(error_msg)
            
            if is_dict:
                state["next_step"] = "end"
            else:
                state.next_step = "end"
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
