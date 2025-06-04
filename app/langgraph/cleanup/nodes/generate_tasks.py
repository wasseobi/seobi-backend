from langchain_core.messages import HumanMessage
from datetime import datetime
import json

from app.langgraph.cleanup.cleanup_state import CleanupState
from app.utils.openai_client import init_langchain_llm
from app.utils.prompt.cleanup_prompts import TASK_GENERATION_PROMPT

class GenerateTasksNode:
    def __init__(self):
        """Initialize the node."""
        self._model = None
        
    @property
    def model(self):
        """Lazy initialization of LLM."""
        if self._model is None:
            self._model = init_langchain_llm()
        return self._model

    def __call__(self, state: CleanupState) -> CleanupState:
        """Generate AI tasks based on conversation analysis"""
        try:
            if not state.get("analysis_result"):
                state["error"] = "No analysis result available for task generation"
                return state
                
            # Get tasks from LLM
            response = self.model.invoke([
                HumanMessage(content=TASK_GENERATION_PROMPT.format(
                    analysis_result=json.dumps(state["analysis_result"], indent=2)
                ))
            ])
            
            # Extract JSON content from code block if present
            content = response.content.strip()
            
            # Remove code block markers if present
            if content.startswith("```json"):
                content = content[7:]  # Remove ```json
            elif content.startswith("```"):
                content = content[3:]  # Remove ```
            if content.endswith("```"):
                content = content[:-3]  # Remove trailing ```
            content = content.strip()  # Remove any extra whitespace

            # Parse the response
            tasks = json.loads(content)
            
            # Update state
            state["generated_tasks"] = tasks
            state["end_time"] = datetime.now()
            return state
            
        except Exception as e:
            state["error"] = f"Error in task generation: {str(e)}"
            return state 