from langchain_core.messages import HumanMessage
from datetime import datetime
import json

from app.langgraph.cleanup.cleanup_state import CleanupState
from app.utils.openai_client import init_langchain_llm
from app.utils.prompt.cleanup_prompts import TASK_GENERATION_PROMPT

class GenerateTasksNode:
    def __init__(self):
        """Initialize the node with default model."""
        self.llm = init_langchain_llm()
        
    def __call__(self, state: CleanupState) -> CleanupState:
        """Generate AI tasks based on conversation analysis"""
        try:
            if not state.get("analysis_result"):
                state["error"] = "No analysis result available for task generation"
                return state
                
            # Get tasks from LLM
            response = self.llm.invoke([
                HumanMessage(content=TASK_GENERATION_PROMPT.format(
                    analysis_result=json.dumps(state["analysis_result"], indent=2)
                ))
            ])
            
            # Parse the response
            tasks = json.loads(response.content)
            
            # Update state
            state["generated_tasks"] = tasks
            state["end_time"] = datetime.now()
            return state
            
        except Exception as e:
            state["error"] = f"Error in task generation: {str(e)}"
            return state 