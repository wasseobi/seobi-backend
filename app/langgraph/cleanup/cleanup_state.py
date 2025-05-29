from typing import TypedDict, List, Optional
from datetime import datetime
import uuid

class CleanupState(TypedDict):
    """State for the cleanup graph"""
    session_id: uuid.UUID
    conversation_history: List[dict]
    analysis_result: Optional[dict]
    generated_tasks: Optional[List[dict]]
    error: Optional[str]
    start_time: datetime
    end_time: Optional[datetime] 