"""LLM 호출 및 응답 생성 모듈."""
from typing import Dict, List, Any
from langchain_core.messages import AIMessage, ToolMessage, BaseMessage, HumanMessage
import json

from ..agent_state import AgentState
from ..prompts.system_prompt import prompt
from ...utils.openai_client import init_langchain_llm
from ..tools import tools
from ...utils.message.converter import convert_to_openai_messages
from ...utils.message.formatter import format_message_content, format_message_list

# 도구가 바인딩된 모델 초기화
model = init_langchain_llm(tools)

def format_tool_results(tool_results: List[Any]) -> Dict:
    """도구 실행 결과를 ToolMessage 형식으로 변환."""
    if not tool_results:
        return None
        
    # 도구 실행 결과를 구조화
    formatted_output = {
        "stdout": "",
        "artifacts": [],
        "status": "success"
    }
    
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

def call_model(state: Dict) -> Dict:
    """LLM을 호출하고 응답을 생성하는 노드."""
    try:
        # 기본 state 구조 확인 및 초기화
        if "messages" not in state:
            state["messages"] = []
        if "current_input" not in state:
            state["current_input"] = ""
            
        # 현재 입력을 메시지로 변환
        if state["current_input"]:
            current_msg = HumanMessage(content=state["current_input"])
            # 현재 입력 메시지를 messages에 바로 추가
            state["messages"].append(current_msg)
            
        # LLM에 전달할 메시지 포맷팅
        formatted_messages = prompt.format_messages(
            messages=state["messages"]
        )
        
        # OpenAI 형식으로 메시지 변환
        openai_messages = convert_to_openai_messages(formatted_messages)
        
        try:
            # LangChain 모델 호출
            response = model.invoke(openai_messages)
            
            # tool_calls 확인 및 처리
            has_tool_calls = (
                hasattr(response, "additional_kwargs") and 
                "tool_calls" in response.additional_kwargs
            )
            
            # 상태 업데이트
            if has_tool_calls:
                state["next_step"] = "tool"
                tool_calls = response.additional_kwargs["tool_calls"]
                state["current_tool_calls"] = tool_calls
                if tool_calls:
                    state["current_tool_call_id"] = tool_calls[0].get("id", "default_call")
                    state["current_tool_name"] = tool_calls[0].get("function", {}).get("name", "tool")
            else:
                state["next_step"] = "end"
            
            # AI 응답을 messages에 추가
            state["messages"].append(response)
            
            # 도구 결과가 있는 경우 ToolMessage로 처리
            if state.get("tool_results"):
                tool_output = format_tool_results(state["tool_results"])
                
                if tool_output:
                    tool_message = ToolMessage(
                        content=tool_output["stdout"],
                        tool_call_id=state.get("current_tool_call_id", "default_call"),
                        name=state.get("current_tool_name", "tool")
                    )
                    state["messages"].append(tool_message)
            
            # 전체 대화 히스토리를 변환된 형식으로 저장
            formatted_messages = format_message_list(state["messages"])
            state["formatted_messages"] = formatted_messages
            
            # 디버그 출력
            # print("\nFormatted Messages:")
            # print(json.dumps(formatted_messages, indent=2, ensure_ascii=False))
            # print(f"\nNext step: {state['next_step']}\n")
            
        except Exception as e:
            error_msg = AIMessage(content=f"죄송합니다. 응답 생성 중 오류가 발생했습니다: {str(e)}")
            state["messages"].append(error_msg)
            state["next_step"] = "end"
            return state
            
    except Exception as e:
        import traceback
        traceback.print_exc()
        state["error"] = str(e)
        state["next_step"] = "end"
        
    return state
