import json
import traceback
from typing import Dict, List
from langchain_core.messages import BaseMessage, FunctionMessage, AIMessage
from langchain_core.tools import BaseTool

def call_tool(state: Dict, tools: List[BaseTool]) -> Dict:
    """도구를 호출하고 결과를 처리하는 노드."""
    
    try:
        # 마지막 AI 메시지에서 도구 호출 정보 추출
        if not state.get("messages"):
            raise ValueError("No messages in state")
            
        last_message = state["messages"][-1]
        
        if hasattr(last_message, "additional_kwargs"):
            print(f"Additional kwargs: {last_message.additional_kwargs}")
            
        # tool_calls 정보 추출 및 검증
        tool_calls = []
        if hasattr(last_message, "additional_kwargs"):
            tool_calls = last_message.additional_kwargs.get("tool_calls", [])
            
        if not tool_calls:
            print("No tool_calls found, returning to model")
            state["next_step"] = "model"
            return state
            
        # 각 tool call 처리
        for tool_call in tool_calls:
            try:
                if not isinstance(tool_call, dict) or "function" not in tool_call:
                    print("Invalid tool call format")
                    continue
                    
                # 도구 호출 정보 추출
                call_id = tool_call.get("id", "")
                function_info = tool_call["function"]
                function_name = function_info.get("name")
                
                # 인자 파싱
                arguments_str = function_info.get("arguments", "{}")
                try:
                    arguments = json.loads(arguments_str)
                    # __arg1 형식 인자 처리
                    if "__arg1" in arguments:
                        arg_value = arguments["__arg1"]
                        if function_name == "search_web":
                            arguments = {"query": arg_value}
                        elif function_name == "calculator":
                            arguments = {"expression": arg_value}
                except json.JSONDecodeError:
                    arguments = {}
                
                # 도구 실행
                tool = next((t for t in tools if t.name == function_name), None)
                if tool:
                    result = tool.invoke(arguments)
                    
                    # FunctionMessage 생성 시 필요한 메타데이터 포함
                    function_message = FunctionMessage(
                        name=function_name,
                        content=str(result),
                        additional_kwargs={
                            "tool_call_id": call_id,
                            "name": function_name,
                            "tool_info": tool_call
                        }
                    )
                    
                    # 메시지 및 scratchpad 업데이트
                    state["messages"].append(function_message)
                    if "scratchpad" in state:
                        state["scratchpad"].append(function_message)
                    
            except Exception as e:
                print(f"Error processing tool call {function_name}: {str(e)}")
                import traceback
                traceback.print_exc()
                # 오류 메시지를 tool 응답으로 추가
                error_message = FunctionMessage(
                    name=function_name,
                    content=f"Error: {str(e)}",
                    additional_kwargs={"tool_call_id": call_id}
                )
                state["messages"].append(error_message)
        
        # 다음 단계를 model로 설정하여 결과 처리
        state["next_step"] = "model"
        return state
        
    except Exception as e:
        print(f"Error in call_tool: {str(e)}")
        import traceback
        traceback.print_exc()
        state["error"] = str(e)
        state["next_step"] = "model"
        return state
