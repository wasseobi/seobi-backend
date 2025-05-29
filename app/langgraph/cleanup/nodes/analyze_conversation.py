from langchain_core.messages import HumanMessage, AIMessage
import json

from app.langgraph.cleanup.cleanup_state import CleanupState
from app.utils.openai_client import init_langchain_llm
from app.utils.prompt.cleanup_prompts import ANALYSIS_PROMPT

class AnalyzeConversationNode:
    def __init__(self):
        """Initialize the node with default model."""
        self.llm = init_langchain_llm()
        
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
            response = self.llm.invoke([
                HumanMessage(content=ANALYSIS_PROMPT),
                *messages
            ])
            
            # Parse the response
            analysis_result = json.loads(response.content)
            
            # Update state
            state["analysis_result"] = analysis_result
            return state
            
        except Exception as e:
            state["error"] = f"Error in conversation analysis: {str(e)}"
            return state 