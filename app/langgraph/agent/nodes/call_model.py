"""LLM 호출 및 응답 생성 모듈."""
from typing import Dict, List, Any
from langchain_core.messages import AIMessage, ToolMessage, BaseMessage, HumanMessage
import json
import logging
import os

from app.utils.openai_client import init_langchain_llm
from app.utils.message.converter import convert_to_openai_messages
from app.utils.message.formatter import format_message_content, format_message_list
from ...tools import agent_tools
from ..agent_state import AgentState
from ....utils.prompt.agent_prompt import prompt

# 도구가 바인딩된 모델 초기화
model = init_langchain_llm(agent_tools)

# 로그 디렉토리 설정
LOG_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))), 'logs')
os.makedirs(LOG_DIR, exist_ok=True)  # logs 폴더가 없으면 생성
LOG_PATH = os.path.join(LOG_DIR, 'langgraph_debug.log')

# 로거 설정
log = logging.getLogger("langgraph_debug")
if not log.handlers:  # 핸들러가 없는 경우에만 추가
    log.setLevel(logging.INFO)
    
    # 파일 핸들러 생성
    file_handler = logging.FileHandler(LOG_PATH, mode='a', encoding='utf-8')
    file_handler.setLevel(logging.INFO)
    
    # 포맷터 설정
    formatter = logging.Formatter('[%(asctime)s] %(message)s')
    file_handler.setFormatter(formatter)
    
    # 핸들러 추가
    log.addHandler(file_handler)
    
    # 로그가 상위 로거로 전파되지 않도록 설정
    log.propagate = False

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
            log.info("[CallModel:format_tool_results] Converted single result to list")

        for result in tool_results:
            log.info(f"[CallModel:format_tool_results] Processing result: {result}")
            log.info(f"[CallModel:format_tool_results] Result type: {type(result)}")
            
            if isinstance(result, dict):
                # 결과가 dict인 경우 artifact로 저장
                formatted_output["artifacts"].append(result)
                if "content" in result:
                    formatted_output["stdout"] += str(result["content"]) + "\n"
                log.info(f"[CallModel:format_tool_results] Added dict result as artifact")
            else:
                # 단순 문자열인 경우 stdout으로 처리
                formatted_output["stdout"] += str(result) + "\n"
                log.info(f"[CallModel:format_tool_results] Added string result to stdout")
                
        log.info(f"[CallModel:format_tool_results] Final formatted output: {formatted_output}")
        return formatted_output
            
    except Exception as e:
        log.error(f"[CallModel:format_tool_results] Error formatting tool results: {str(e)}", exc_info=True)
        formatted_output["status"] = "error"
        formatted_output["stdout"] = f"Error formatting tool results: {str(e)}"
        return formatted_output

def call_model(state: AgentState) -> AgentState:
    """LLM을 호출하고 응답을 생성하는 노드."""
    try:
        # 기본 state 구조 확인 및 초기화
        if not hasattr(state, "messages"):
            state.messages = []
        if not hasattr(state, "current_input"):
            state.current_input = ""
            
        # 현재 입력을 메시지로 변환 - 현재 사이클에서 처음 한 번만
        if state.current_input and not getattr(state, "input_processed", False):
            current_msg = HumanMessage(content=state.current_input)
            state.messages.append(current_msg)
            state.input_processed = True
            log.info(f"[CallModel] Added HumanMessage: {state.current_input}")
            
        # 이전 도구 실행 결과 처리
        log.info(f"[CallModel] Checking tool results state - has_attr: {hasattr(state, 'tool_results')}, tool_results: {getattr(state, 'tool_results', None)}")
        if hasattr(state, "tool_results") and state.tool_results:
            tool_output = format_tool_results(state.tool_results)
            log.info(f"[CallModel] Processing tool output: {tool_output}")
            
            if tool_output:
                log.info(f"[CallModel] Current tool state - ID: {getattr(state, 'current_tool_call_id', None)}, Name: {getattr(state, 'current_tool_name', None)}")
                if state.current_tool_call_id and state.current_tool_name:
                    tool_message = ToolMessage(
                        content=tool_output["stdout"],
                        tool_call_id=state.current_tool_call_id,
                        name=state.current_tool_name
                    )
                    state.messages.append(tool_message)
                    log.info(f"[CallModel] Successfully added ToolMessage - ID: {state.current_tool_call_id}, Name: {state.current_tool_name}")
                    log.info(f"[CallModel] Current messages count: {len(state.messages)}, Last message type: {type(state.messages[-1])}")
                else:
                    log.warning("[CallModel] Missing tool_call_id or tool_name, cannot create ToolMessage")
            else:
                log.warning("[CallModel] Tool output is empty or invalid")
            
            # 도구 관련 상태 초기화
            state.clear_tool_state()
            log.info("[CallModel] Cleared tool state")
            
        # LLM에 전달할 메시지 포맷팅
        formatted_messages = prompt.format_messages(
            messages=state.messages
        )
        
        # OpenAI 형식으로 메시지 변환
        openai_messages = convert_to_openai_messages(formatted_messages)
        log.info(f"[CallModel] Sending {len(openai_messages)} messages to LLM")
        log.info(f"[CallModel] Messages to send: {openai_messages}")
        
        try:
            # LangChain 모델 호출
            response = model.invoke(openai_messages)
            log.info(f"[CallModel] Received response: {response}")
            
            # tool_calls 확인 및 처리
            has_tool_calls = (
                hasattr(response, "additional_kwargs") and 
                "tool_calls" in response.additional_kwargs and
                response.additional_kwargs["tool_calls"]
            )
            
            # 상태 업데이트
            if has_tool_calls:
                tool_calls = response.additional_kwargs["tool_calls"]
                log.info(f"[CallModel] Found tool_calls in response: {tool_calls}")
                state.next_step = "tool"
                # tool 정보 설정
                state.set_tool_info(tool_calls)
            else:
                state.next_step = "end"
            
            # AI 응답을 messages에 추가
            state.messages.append(response)
            state.step_count += 1
            log.info(f"[CallModel] Added AI response, current message count: {len(state.messages)}")
            
        except Exception as e:
            log.error(f"[CallModel] Exception in LLM/tool: {e}", exc_info=True)
            error_msg = AIMessage(content=f"죄송합니다. 응답 생성 중 오류가 발생했습니다: {str(e)}")
            state.messages.append(error_msg)
            state.next_step = "end"
            return state
            
    except Exception as e:
        log.error(f"[CallModel] Outer exception:", exc_info=True)
        state.error = str(e)
        state.next_step = "end"
        
    return state
