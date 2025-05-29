from app.dao.base import BaseDAO
from app.models import Schedule, db
from typing import List, Optional
import uuid


class ScheduleDAO(BaseDAO[Schedule]):
    """Data Access Object for Schedule model"""
    def __init__(self):
        super().__init__(Schedule)

    def get_all_schedules(self) -> List[Schedule]:
        """Get all schedules ordered by timestamp asc"""
        return self.query().order_by(Schedule.timestamp.asc()).all()

    def get_schedule_by_id(self, schedule_id: uuid.UUID) -> Optional[Schedule]:
        """Get a schedule by ID"""
        return self.get(str(schedule_id))

    def get_user_schedules(self, user_id: uuid.UUID) -> List[Schedule]:
        """Get all schedules for a user ordered by timestamp asc"""
        return self.query().filter_by(user_id=user_id).order_by(Schedule.timestamp.asc()).all()

    def create(self, user_id: uuid.UUID, **kwargs) -> Schedule:
        """Create a new schedule with user_id"""
        return super().create(user_id=user_id, **kwargs)

    def update_schedule(self, schedule_id: uuid.UUID, **kwargs) -> Optional[Schedule]:
        """Update a schedule with specific fields"""
        return self.update(str(schedule_id), **kwargs)

    def delete(self, schedule_id: uuid.UUID) -> bool:
        """Delete a schedule"""
        return super().delete(str(schedule_id))