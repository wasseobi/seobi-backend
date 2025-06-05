import uuid
from datetime import datetime
from typing import List, Optional

from app.models import Schedule
from app.dao.base import BaseDAO

class ScheduleDAO(BaseDAO[Schedule]):
    """Data Access Object for Schedule model"""
    def __init__(self):
        super().__init__(Schedule)

    def get_all(self) -> List[Schedule]:
        """Get all schedules ordered by timestamp asc"""
        return self.query().order_by(Schedule.timestamp.asc()).all()

    def get_by_id(self, schedule_id: uuid.UUID) -> Optional[Schedule]:
        """Get a schedule by ID"""
        return self.get(str(schedule_id))

    def get_all_by_user_id(self, user_id: uuid.UUID) -> List[Schedule]:
        """Get all schedules for a user ordered by timestamp asc"""
        return self.query().filter_by(user_id=user_id).order_by(Schedule.timestamp.asc()).all()

    def get_all_by_user_id_in_range_status(self, user_id: uuid.UUID, start: datetime, end: datetime, status=None) -> List[Schedule]:
        """Get all schedules for a user in a given datetime range, optionally filtered by status."""
        query = self.query().filter_by(user_id=user_id)
        query = query.filter(self.model.start_at >= start, self.model.start_at < end)
        if status:
            query = query.filter_by(status=status)
        return query.order_by(self.model.timestamp.asc()).all()

    def get_count_by_date_range(self, user_id: uuid.UUID, start: datetime, end: datetime, status=None) -> int:
        """Get the count of schedules for a user in a given datetime range, optionally filtered by status."""
        query = self.query().filter_by(user_id=user_id)
        query = query.filter(self.model.start_at >= start, self.model.start_at < end)
        if status:
            query = query.filter_by(status=status)
        return query.count()

    def get_all_by_ongoing(self, user_id: uuid.UUID, current_time: datetime) -> List[Schedule]:
        """현재 진행 중인 일정 조회 (시작했지만 아직 완료되지 않은 일정)"""
        return (self.query()
                .filter_by(user_id=user_id)
                .filter(self.model.start_at <= current_time)
                .filter(self.model.is_completed == False)
                .order_by(self.model.start_at.asc())
                .all())

    def create(self, user_id: uuid.UUID, **kwargs) -> Schedule:
        return super().create(user_id=user_id, **kwargs)

    def update(self, schedule_id: uuid.UUID, **kwargs) -> Optional[Schedule]:
        """Update a schedule with specific fields"""
        return super().update(str(schedule_id), **kwargs)