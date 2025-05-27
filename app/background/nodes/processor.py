"""Conversation processor node implementation."""
from typing import Dict, Any, List
from langchain.schema import BaseMessage
from flask import current_app

from app.models.message import Message
from app.models.session import Session
from app.models.db import db


async def conversation_processor_node(state: Dict[str, Any]) -> Dict[str, Any]:
    """Process a completed conversation.
    
    This node is responsible for initial processing of a completed conversation,
    such as:
    - Validating the conversation data
    - Preparing the data for analysis
    - Determining what additional processing is needed
    
    Args:
        state: Current state dictionary containing:
            - conversation_id: ID of the conversation to process
            - messages: List of messages in the conversation
            
    Returns:
        Updated state dictionary with:
            - next_step: Next processing step ("analyze", "summarize", or "end")
            - error: Error message if processing failed
            - processed_data: Processed conversation data
    """
    try:
        conversation_id = state.get("conversation_id")
        messages = state.get("messages", [])
        
        if not conversation_id or not messages:
            return {
                "error": "Missing conversation_id or messages",
                "next_step": "end"
            }
            
        # Get session from database
        session = Session.query.get(conversation_id)
        if not session:
            return {
                "error": f"Session {conversation_id} not found",
                "next_step": "end"
            }
            
        # Process messages
        processed_messages = []
        for msg in messages:
            # Convert message to database model if needed
            if isinstance(msg, dict):
                message = Message(
                    session_id=conversation_id,
                    role=msg.get("role"),
                    content=msg.get("content"),
                    timestamp=msg.get("timestamp")
                )
                db.session.add(message)
                processed_messages.append(message)
            else:
                processed_messages.append(msg)
                
        # Commit changes to database
        db.session.commit()
        
        # Determine next step based on conversation characteristics
        next_step = "analyze"  # Default to analysis
        
        # Update state with processed data
        return {
            "next_step": next_step,
            "processed_data": {
                "session": session,
                "messages": processed_messages
            }
        }
        
    except Exception as e:
        current_app.logger.error(f"Error in conversation processor: {str(e)}")
        return {
            "error": str(e),
            "next_step": "end"
        } 