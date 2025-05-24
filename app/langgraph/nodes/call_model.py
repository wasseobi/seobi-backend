"""LLM 호출 및 응답 생성 모듈."""
from typing import Dict
from langchain_core.messages import AIMessage
from dotenv import load_dotenv
import os

from ..agent_state import AgentState
from ..prompts.system_prompt import prompt
from ..llm_config import model  # llm_config에서 설정된 모델 가져오기
from ..utils.message_converter import convert_to_openai_messages

# 환경 변수 로드
load_dotenv()

def call_model(state: Dict) -> Dict:
    """LLM을 호출하고 응답을 생성하는 노드."""
    try:
        print("\n=== Call Model Node ===")
        print(f"현재 상태:\n- 입력: {state.get('current_input')}")
        print(f"- 메시지 수: {len(state.get('messages', []))}")
        print(f"- 도구 결과 존재: {bool(state.get('tool_results'))}")
        
        # 기본 state 구조 확인
        if "messages" not in state:
            state["messages"] = []
        if "scratchpad" not in state:
            state["scratchpad"] = []
        if "current_input" not in state:
            state["current_input"] = ""
            
        # 메시지 포맷팅
        formatted_messages = prompt.format_messages(
            messages=state["messages"],
            input=state["current_input"],
            scratchpad=state["scratchpad"]
        )
        
        # 도구 결과가 있는 경우 처리
        if state.get("tool_results"):
            print("\n[디버그] 도구 실행 결과 처리")
            print(f"도구 결과: {state['tool_results'][:200]}...")
            
            # 도구 결과를 시스템 메시지로 변환
            result_content = "검색 결과:\n"
            for result in state["tool_results"]:
                if isinstance(result, dict):
                    result_content += str(result.get("content", "")) + "\n"
                else:
                    result_content += str(result) + "\n"
            
            formatted_messages.append({
                "role": "system",
                "content": f"다음 검색 결과를 참고하여 응답해주세요: {result_content}"
            })
            print("\n[디버그] 시스템 메시지 추가됨")
            
        # OpenAI 형식으로 메시지 변환
        openai_messages = convert_to_openai_messages(formatted_messages)
        print("\n[디버그] 변환된 메시지 수:", len(openai_messages))
        
        try:
            # LangChain 모델 호출
            print("\n[디버그] 모델 호출 시작")
            response = model.invoke(openai_messages)
            print(f"[디버그] 모델 응답: {response.content[:200]}...")
            
            # tool_calls 확인
            has_tool_calls = (
                hasattr(response, "additional_kwargs") and 
                "tool_calls" in response.additional_kwargs
            )
            print(f"[디버그] 도구 호출 필요: {has_tool_calls}")
            
            # 상태 업데이트
            if has_tool_calls:
                state["next_step"] = "tool"
                state["current_tool_calls"] = response.additional_kwargs["tool_calls"]
            else:
                state["next_step"] = "end"
            
            # AI 메시지 추가
            state["messages"].append(response)
            print("[디버그] 상태 업데이트 완료")
            
        except Exception as e:
            print(f"[에러] 모델 호출 중 오류: {str(e)}")
            error_msg = AIMessage(content=f"죄송합니다. 응답 생성 중 오류가 발생했습니다: {str(e)}")
            state["messages"].append(error_msg)
            state["next_step"] = "end"
        
        return state
        
    except Exception as e:
        print(f"[에러] call_model 함수 오류: {str(e)}")
        import traceback
        traceback.print_exc()
        state["error"] = str(e)
        state["next_step"] = "end"
        return state
