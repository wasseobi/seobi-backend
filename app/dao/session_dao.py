from app.dao.base import BaseDAO
from app.models import db, Session
from datetime import datetime, timezone, timedelta
from typing import List, Optional
import uuid

class SessionDAO(BaseDAO[Session]):
    """Data Access Object for Session model"""
    
    def __init__(self):
        super().__init__(Session)

    def get_all_sessions(self) -> List[Session]:
        """Get all sessions ordered by start time"""
        return self.query().order_by(Session.start_at.desc()).all()
    
    def get_session_by_id(self, session_id: uuid.UUID) -> Optional[Session]:
        """Get a session by ID"""
        return self.get(str(session_id))
       
    def get_user_sessions(self, user_id: uuid.UUID) -> List[Session]:
        """Get all sessions for a user ordered by creation time"""
        return self.query().filter_by(user_id=user_id).order_by(Session.start_at.desc()).all()
 
    def create(self, user_id: uuid.UUID) -> Session:
        """Create a new session with user_id"""
        return super().create(user_id=user_id)
    
    def update_session(self, session_id: uuid.UUID, **kwargs) -> Optional[Session]:
        """Update a session with specific fields"""
        return self.update(str(session_id), **kwargs)

    def update_finish_time(self, session_id: uuid.UUID, finish_time: datetime) -> Optional[Session]:
        """Update session finish time"""
        return self.update_session(session_id, finish_at=finish_time)

    def get_user_id_by_session_id(self, session_id: uuid.UUID) -> Optional[uuid.UUID]:
        """Get user_id by session_id"""
        session = self.get_session_by_id(session_id)
        if session:
            return session.user_id
        return None
