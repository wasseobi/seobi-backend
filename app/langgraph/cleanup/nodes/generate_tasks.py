from langchain_core.messages import HumanMessage
from datetime import datetime
import json
import re

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
                
            # Check if analysis result is empty
            analysis = state["analysis_result"]
            print(f"[GenerateTasksNode] analysis: {analysis}")
                # If all arrays are empty, set generated_tasks to empty list and end
            if not analysis.get("content") :
                # If all arrays are empty, set generated_tasks to empty list and end
                state["generated_tasks"] = []
                state["end_time"] = datetime.now()
                return state
                
            try:
                analysis_json = json.dumps(state["analysis_result"], indent=2)
            except Exception as e:
                print(f"[GenerateTasksNode] analysis_result 직렬화 에러: {str(e)}")
                state["error"] = f"Error in analysis_result serialization: {str(e)}"
                return state

            prompt = TASK_GENERATION_PROMPT.format(
                analysis_result=analysis_json
            )

            try:
                response = self.model.invoke([HumanMessage(content=prompt)])
            except Exception as e:
                print(f"[GenerateTasksNode] LLM 호출 에러: {str(e)}")
                state["error"] = f"Error in LLM call: {str(e)}"
                return state

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

            try:
                tasks = json.loads(content)
                if not isinstance(tasks, list):
                    raise ValueError("LLM 응답이 리스트가 아님")
                for task in tasks:
                    if not isinstance(task, dict) or "title" not in task:
                        raise ValueError(f"잘못된 task 형식: {task}")
            except Exception as e:
                print(f"[GenerateTasksNode] tasks 파싱/검증 에러: {str(e)}")
                state["error"] = f"Error in task parsing/validation: {str(e)}"
                return state

            # Update state
            state["generated_tasks"] = tasks
            state["end_time"] = datetime.now()
            return state
            
        except Exception as e:
            state["error"] = f"Error in task generation: {str(e)}"
            return state 