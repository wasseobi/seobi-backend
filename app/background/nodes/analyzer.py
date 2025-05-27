"""Conversation analyzer node implementation."""
from typing import Dict, Any, List
from datetime import datetime
from flask import current_app
from langchain.chat_models import ChatOpenAI
from langchain.prompts import ChatPromptTemplate
import json

from ..state import BackgroundState, AnalysisResults, AnalysisMetadata


async def conversation_analyzer_node(state: BackgroundState) -> BackgroundState:
    """Analyze a processed conversation.
    
    This node performs analysis on the processed conversation, such as:
    - Sentiment analysis
    - Topic extraction
    - Key points identification
    - User intent analysis
    
    Args:
        state: Current background processing state
        
    Returns:
        Updated background processing state
    """
    try:
        processed_data = state.get("processed_data", {})
        if not processed_data:
            return {
                **state,
                "error": "No processed data available",
                "next_step": "end"
            }
            
        messages = processed_data.get("messages", [])
        metadata = processed_data.get("metadata", {})
        
        if not messages:
            return {
                **state,
                "error": "No messages available for analysis",
                "next_step": "end"
            }
            
        # Initialize LLM
        llm = ChatOpenAI(
            temperature=0,
            model_name="gpt-3.5-turbo"
        )
        
        # Create analysis prompt
        analysis_prompt = ChatPromptTemplate.from_messages([
            ("system", """You are an expert conversation analyzer. Analyze the following conversation and provide:
            1. Main topics discussed
            2. Key points made
            3. User's primary intent
            4. Overall sentiment
            5. Action items or follow-ups needed
            
            Additional context about the conversation:
            - Total messages: {message_count}
            - Time span: {time_span}
            - Participants: {participants}
            
            Format your response as a JSON object with these keys:
            - topics: list of main topics
            - key_points: list of key points
            - user_intent: string describing primary intent
            - sentiment: string (positive, negative, neutral, or mixed)
            - action_items: list of action items
            - confidence: float between 0 and 1 indicating analysis confidence
            """),
            ("user", "{conversation}")
        ])
        
        # Format conversation for analysis
        conversation_text = "\n".join([
            f"{msg['role']}: {msg['content']}"
            for msg in messages
        ])
        
        # Calculate time span
        time_span = "Unknown"
        if metadata.get("first_message_time") and metadata.get("last_message_time"):
            first_time = datetime.fromisoformat(metadata["first_message_time"])
            last_time = datetime.fromisoformat(metadata["last_message_time"])
            time_span = f"{last_time - first_time}"
            
        # Run analysis
        chain = analysis_prompt | llm
        analysis_result = await chain.ainvoke({
            "conversation": conversation_text,
            "message_count": metadata.get("message_count", 0),
            "time_span": time_span,
            "participants": ", ".join(metadata.get("unique_roles", []))
        })
        
        # Parse analysis results
        try:
            analysis_data: AnalysisResults = json.loads(analysis_result.content)
        except json.JSONDecodeError:
            current_app.logger.warning("Failed to parse analysis results as JSON")
            analysis_data = {
                "topics": [],
                "key_points": [],
                "user_intent": "Unknown",
                "sentiment": "Unknown",
                "action_items": [],
                "confidence": 0.0
            }
            
        # Add analysis metadata
        analysis_metadata: AnalysisMetadata = {
            "analyzed_at": datetime.now().isoformat(),
            "model_used": "gpt-3.5-turbo",
            "confidence": analysis_data.get("confidence", 0.0),
            "analysis_version": "1.0"
        }
        
        return {
            **state,
            "next_step": "summarize",
            "analysis_results": analysis_data,
            "analysis_metadata": analysis_metadata
        }
        
    except Exception as e:
        current_app.logger.error(f"Error in conversation analyzer: {str(e)}")
        return {
            **state,
            "error": str(e),
            "next_step": "end"
        } 