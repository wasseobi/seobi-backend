"""Conversation summarizer node implementation."""
from typing import Dict, Any, List
from datetime import datetime
from flask import current_app
from langchain.chat_models import ChatOpenAI
from langchain.prompts import ChatPromptTemplate
import json

from ..state import BackgroundState, SummaryResults


async def conversation_summarizer_node(state: BackgroundState) -> BackgroundState:
    """Summarize a processed and analyzed conversation.
    
    This node creates a concise summary of the conversation, incorporating
    the analysis results to provide a comprehensive overview.
    
    Args:
        state: Current background processing state
        
    Returns:
        Updated background processing state
    """
    try:
        processed_data = state.get("processed_data", {})
        analysis_results = state.get("analysis_results", {})
        analysis_metadata = state.get("analysis_metadata", {})
        
        if not processed_data or not analysis_results:
            return {
                **state,
                "error": "Missing processed data or analysis results",
                "next_step": "end"
            }
            
        messages = processed_data.get("messages", [])
        conversation_metadata = processed_data.get("metadata", {})
        
        if not messages:
            return {
                **state,
                "error": "No messages available for summarization",
                "next_step": "end"
            }
            
        # Initialize LLM
        llm = ChatOpenAI(
            temperature=0,
            model_name="gpt-3.5-turbo"
        )
        
        # Create summarization prompt
        summary_prompt = ChatPromptTemplate.from_messages([
            ("system", """You are an expert conversation summarizer. Create a concise summary of the following conversation,
            incorporating the provided analysis results. The summary should:
            1. Capture the main points of the conversation
            2. Include key decisions or agreements
            3. Highlight any action items
            4. Be clear and easy to understand
            5. Be no longer than 3 paragraphs
            
            Additional context:
            - Analysis confidence: {confidence}
            - Main topics: {topics}
            - User intent: {user_intent}
            - Sentiment: {sentiment}
            
            Format your response as a JSON object with these keys:
            - summary: string containing the main summary
            - key_decisions: list of key decisions or agreements
            - action_items: list of specific action items
            - confidence: float between 0 and 1 indicating summary confidence
            """),
            ("user", "Conversation:\n{conversation}\n\nAnalysis Results:\n{analysis}")
        ])
        
        # Format conversation for summarization
        conversation_text = "\n".join([
            f"{msg['role']}: {msg['content']}"
            for msg in messages
        ])
        
        # Run summarization
        chain = summary_prompt | llm
        summary_result = await chain.ainvoke({
            "conversation": conversation_text,
            "analysis": json.dumps(analysis_results, indent=2),
            "confidence": analysis_metadata.get("confidence", 0.0),
            "topics": ", ".join(analysis_results.get("topics", [])),
            "user_intent": analysis_results.get("user_intent", "Unknown"),
            "sentiment": analysis_results.get("sentiment", "Unknown")
        })
        
        # Parse summary results
        try:
            summary_data: SummaryResults = json.loads(summary_result.content)
        except json.JSONDecodeError:
            current_app.logger.warning("Failed to parse summary results as JSON")
            summary_data = {
                "summary": "Failed to generate summary",
                "key_decisions": [],
                "action_items": [],
                "confidence": 0.0
            }
            
        # Create final result
        final_result = {
            "conversation_id": processed_data["conversation_id"],
            "summary": summary_data,
            "analysis": analysis_results,
            "metadata": {
                **conversation_metadata,
                **analysis_metadata,
                "summarized_at": datetime.now().isoformat(),
                "summary_confidence": summary_data.get("confidence", 0.0),
                "summary_version": "1.0"
            }
        }
        
        return {
            **state,
            "next_step": "end",
            "summary_results": summary_data,
            "final_result": final_result
        }
        
    except Exception as e:
        current_app.logger.error(f"Error in conversation summarizer: {str(e)}")
        return {
            **state,
            "error": str(e),
            "next_step": "end"
        } 