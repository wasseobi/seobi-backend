from app.dao.base import BaseDAO
from app.models import AutoTask, db
from typing import List, Optional
from datetime import datetime
import uuid


class AutoTaskDAO(BaseDAO[AutoTask]):
    """Data Access Object for AutoTask model"""
    def __init__(self):
        super().__init__(AutoTask)

    def get_all_auto_tasks(self) -> List[AutoTask]:
        """Get all auto_tasks ordered by created_at asc"""
        return self.query().order_by(AutoTask.created_at.asc()).all()

    def get_auto_task_by_id(self, auto_task_id: uuid.UUID) -> Optional[AutoTask]:
        return self.get(auto_task_id)

    def get_user_auto_tasks(self, user_id: uuid.UUID) -> List[AutoTask]:
        """Get all auto_tasks for a user ordered by created_at asc"""
        return self.query().filter_by(user_id=user_id).order_by(AutoTask.created_at.desc()).all()

    def get_all_by_user_id_in_range(self, user_id: uuid.UUID, start, end, status=None) -> List[AutoTask]:
        """Get all auto_tasks for a user in a given datetime range, optionally filtered by status."""
        query = self.query().filter_by(user_id=user_id)
        query = query.filter(self.model.start_at >= start, self.model.start_at < end)
        if status:
            query = query.filter_by(status=status)
        return query.order_by(self.model.start_at.asc()).all()

    def create(self, user_id: uuid.UUID, **kwargs) -> AutoTask:
        return super().create(user_id=user_id, **kwargs)

    def update(self, auto_task_id: uuid.UUID, **kwargs) -> Optional[AutoTask]:
        return super().update(auto_task_id, **kwargs)

    def update_finish_time(self, auto_task_id: uuid.UUID, finish_time: datetime) -> Optional[AutoTask]:
        return self.update(auto_task_id, finish_at=finish_time)

    def update_status(self, auto_task_id: uuid.UUID, status: str) -> Optional[AutoTask]:
        return self.update(auto_task_id, status=status)

    def delete(self, auto_task_id: uuid.UUID) -> bool:
        return super().delete(auto_task_id)
