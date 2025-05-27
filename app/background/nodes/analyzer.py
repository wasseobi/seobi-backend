"""Conversation analyzer node implementation."""
from typing import Dict, Any, List
from flask import current_app
from langchain.chat_models import ChatOpenAI
from langchain.prompts import ChatPromptTemplate

from app.models.session import Session
from app.models.db import db


async def conversation_analyzer_node(state: Dict[str, Any]) -> Dict[str, Any]:
    """Analyze a processed conversation.
    
    This node performs analysis on the processed conversation, such as:
    - Sentiment analysis
    - Topic extraction
    - Key points identification
    - User intent analysis
    
    Args:
        state: Current state dictionary containing:
            - processed_data: Data from the processor node
            - conversation_id: ID of the conversation
            
    Returns:
        Updated state dictionary with:
            - next_step: Next processing step ("summarize" or "end")
            - error: Error message if analysis failed
            - analysis_results: Results of the conversation analysis
    """
    try:
        processed_data = state.get("processed_data", {})
        if not processed_data:
            return {
                "error": "No processed data available",
                "next_step": "end"
            }
            
        session = processed_data.get("session")
        messages = processed_data.get("messages", [])
        
        if not session or not messages:
            return {
                "error": "Missing session or messages in processed data",
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
            
            Format your response as a JSON object with these keys:
            - topics: list of main topics
            - key_points: list of key points
            - user_intent: string describing primary intent
            - sentiment: string (positive, negative, neutral, or mixed)
            - action_items: list of action items
            """),
            ("user", "{conversation}")
        ])
        
        # Format conversation for analysis
        conversation_text = "\n".join([
            f"{msg.role}: {msg.content}"
            for msg in messages
        ])
        
        # Run analysis
        chain = analysis_prompt | llm
        analysis_result = await chain.ainvoke({
            "conversation": conversation_text
        })
        
        # Parse and store analysis results
        # TODO: Create an AnalysisResult model to store this
        session.analysis_results = analysis_result.content
        db.session.commit()
        
        # Determine next step
        next_step = "summarize"  # Default to summarization
        
        return {
            "next_step": next_step,
            "analysis_results": analysis_result.content,
            "processed_data": processed_data  # Pass through processed data
        }
        
    except Exception as e:
        current_app.logger.error(f"Error in conversation analyzer: {str(e)}")
        return {
            "error": str(e),
            "next_step": "end"
        } 