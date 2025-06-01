import uuid
from datetime import datetime
from typing import List, Optional

from app.models import Schedule
from app.dao.base import BaseDAO

class ScheduleDAO(BaseDAO[Schedule]):
    """Data Access Object for Schedule model"""
    def __init__(self):
        super().__init__(Schedule)

    def get_by_id(self, schedule_id: uuid.UUID) -> Optional[Schedule]:
        """Get a schedule by ID"""
        return self.get(str(schedule_id))

    def get_all(self) -> List[Schedule]:
        """Get all schedules ordered by timestamp asc"""
        return self.query().order_by(Schedule.timestamp.asc()).all()

    def get_all_by_user_id(self, user_id: uuid.UUID) -> List[Schedule]:
        """Get all schedules for a user ordered by timestamp asc"""
        return self.query().filter_by(user_id=user_id).order_by(Schedule.timestamp.asc()).all()

    def get_all_by_user_id_in_range(self, user_id: uuid.UUID, start: datetime, end: datetime, status=None) -> List[Schedule]:
        """Get all schedules for a user in a given datetime range, optionally filtered by status."""
        query = self.query().filter_by(user_id=user_id)
        query = query.filter(self.model.start_at >= start, self.model.start_at < end)
        if status:
            query = query.filter_by(status=status)
        return query.order_by(self.model.timestamp.asc()).all()

    def create(self, user_id: uuid.UUID, **kwargs) -> Schedule:
        return super().create(user_id=user_id, **kwargs)

    def update(self, schedule_id: uuid.UUID, **kwargs) -> Optional[Schedule]:
        """Update a schedule with specific fields"""
        return super().update(str(schedule_id), **kwargs)
