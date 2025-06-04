from langchain_core.messages import HumanMessage, AIMessage
import json

from app.langgraph.cleanup.cleanup_state import CleanupState
from app.utils.openai_client import init_langchain_llm
from app.utils.prompt.cleanup_prompts import ANALYSIS_PROMPT

class AnalyzeConversationNode:
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
        """Analyze the conversation and extract key insights"""
        try:
            # Convert conversation history to messages
            messages = []
            for msg in state["conversation_history"]:
                if msg["role"] == "user":
                    messages.append(HumanMessage(content=msg["content"]))
                else:
                    messages.append(AIMessage(content=msg["content"]))
            
            # Get analysis from LLM
            response = self.model.invoke([
                HumanMessage(content=ANALYSIS_PROMPT),
                *messages
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
            try:
                analysis_result = json.loads(content)
                print(f"Analysis result: {analysis_result}")
            except json.JSONDecodeError as e:
                print(f"JSON Parse Error: {str(e)}")
                print(f"Raw content: {content}")
                state["error"] = f"Error in conversation analysis: {str(e)}"
                return state
            
            # Update state
            state["analysis_result"] = analysis_result
            return state
            
        except Exception as e:
            state["error"] = f"Error in conversation analysis: {str(e)}"
            return state 