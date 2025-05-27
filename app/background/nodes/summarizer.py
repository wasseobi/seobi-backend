"""Conversation summarizer node implementation."""
from typing import Dict, Any, List
from flask import current_app
from langchain.chat_models import ChatOpenAI
from langchain.prompts import ChatPromptTemplate

from app.models.session import Session
from app.models.db import db


async def conversation_summarizer_node(state: Dict[str, Any]) -> Dict[str, Any]:
    """Summarize a processed and analyzed conversation.
    
    This node creates a concise summary of the conversation, incorporating
    the analysis results to provide a comprehensive overview.
    
    Args:
        state: Current state dictionary containing:
            - processed_data: Data from the processor node
            - analysis_results: Results from the analyzer node
            - conversation_id: ID of the conversation
            
    Returns:
        Updated state dictionary with:
            - next_step: Always "end" for this node
            - error: Error message if summarization failed
            - summary: Generated conversation summary
    """
    try:
        processed_data = state.get("processed_data", {})
        analysis_results = state.get("analysis_results")
        
        if not processed_data or not analysis_results:
            return {
                "error": "Missing processed data or analysis results",
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
        
        # Create summarization prompt
        summary_prompt = ChatPromptTemplate.from_messages([
            ("system", """You are an expert conversation summarizer. Create a concise summary of the following conversation,
            incorporating the provided analysis results. The summary should:
            1. Capture the main points of the conversation
            2. Include key decisions or agreements
            3. Highlight any action items
            4. Be clear and easy to understand
            5. Be no longer than 3 paragraphs
            
            Format your response as a JSON object with these keys:
            - summary: string containing the main summary
            - key_decisions: list of key decisions or agreements
            - action_items: list of specific action items
            """),
            ("user", "Conversation:\n{conversation}\n\nAnalysis Results:\n{analysis}")
        ])
        
        # Format conversation for summarization
        conversation_text = "\n".join([
            f"{msg.role}: {msg.content}"
            for msg in messages
        ])
        
        # Run summarization
        chain = summary_prompt | llm
        summary_result = await chain.ainvoke({
            "conversation": conversation_text,
            "analysis": analysis_results
        })
        
        # Store summary in session
        session.summary = summary_result.content
        db.session.commit()
        
        return {
            "next_step": "end",
            "summary": summary_result.content
        }
        
    except Exception as e:
        current_app.logger.error(f"Error in conversation summarizer: {str(e)}")
        return {
            "error": str(e),
            "next_step": "end"
        } 