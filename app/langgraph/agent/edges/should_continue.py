from typing import Dict, List, TypedDict, Annotated
from langchain_core.messages import BaseMessage
from langchain_core.runnables import RunnableConfig, RunnableLambda

def should_continue(state: Dict) -> str:
    """다음 단계를 결정하는 엣지 함수."""
    print("\n=== Router Debug ===")
    print("State:", state)
    
    try:
        if not state.get("messages"):
            print("No messages in state")
            return "continue"
            
        last_message = state["messages"][-1]
        print("Last message:", last_message)
        
        # function_call 확인
        if hasattr(last_message, "additional_kwargs"):
            # function_call이 있는 경우
            if "function_call" in last_message.additional_kwargs:
                function_call = last_message.additional_kwargs.get("function_call")
                if function_call and isinstance(function_call, dict):
                    print("Function call found, routing to: tool")
                    return "tool"
                    
        print("No function calls, continuing")
        return "continue"
        
    except Exception as e:
        print(f"\nError in router: {type(e)} - {str(e)}")
        print("Failsafe: continuing")
        return "continue"

# Runnable 객체로 변환
should_continue_runnable = RunnableLambda(should_continue)
