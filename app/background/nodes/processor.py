"""Conversation processor node implementation."""
from typing import Dict, Any, List
from datetime import datetime
from flask import current_app

from ..state import BackgroundState, ProcessedMessage, ConversationMetadata


async def conversation_processor_node(state: BackgroundState) -> BackgroundState:
    """Process a completed conversation.
    
    This node is responsible for initial processing of a completed conversation,
    such as:
    - Validating the conversation data
    - Preparing the data for analysis
    - Determining what additional processing is needed
    
    Args:
        state: Current background processing state
        
    Returns:
        Updated background processing state
    """
    try:
        conversation_id = state["conversation_id"]
        messages = state["messages"]
        initial_metadata = state["metadata"]
        
        if not conversation_id or not messages:
            return {
                **state,
                "error": "Missing conversation_id or messages",
                "next_step": "end"
            }
            
        # Normalize and validate messages
        processed_messages: List[ProcessedMessage] = []
        for msg in messages:
            if not isinstance(msg, dict):
                continue
                
            processed_msg: ProcessedMessage = {
                "role": msg.get("role", "unknown"),
                "content": msg.get("content", ""),
                "timestamp": msg.get("timestamp") or datetime.now().isoformat()
            }
            
            # Skip empty messages
            if not processed_msg["content"].strip():
                continue
                
            processed_messages.append(processed_msg)
            
        if not processed_messages:
            return {
                **state,
                "error": "No valid messages found in conversation",
                "next_step": "end"
            }
            
        # Generate metadata about the conversation
        metadata: ConversationMetadata = {
            **initial_metadata,
            "message_count": len(processed_messages),
            "has_user_messages": any(msg["role"] == "user" for msg in processed_messages),
            "has_assistant_messages": any(msg["role"] == "assistant" for msg in processed_messages),
            "first_message_time": min(msg["timestamp"] for msg in processed_messages),
            "last_message_time": max(msg["timestamp"] for msg in processed_messages),
            "processed_at": datetime.now().isoformat(),
            "unique_roles": list(set(msg["role"] for msg in processed_messages))
        }
        
        # Update state with processed data
        return {
            **state,
            "next_step": "analyze",
            "processed_data": {
                "conversation_id": conversation_id,
                "messages": processed_messages,
                "metadata": metadata
            }
        }
        
    except Exception as e:
        current_app.logger.error(f"Error in conversation processor: {str(e)}")
        return {
            **state,
            "error": str(e),
            "next_step": "end"
        } 