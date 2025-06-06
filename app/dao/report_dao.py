from datetime import datetime
from typing import List, Optional
import uuid
from app.models import Report
from app.dao.base import BaseDAO

class ReportDAO(BaseDAO[Report]):
    def __init__(self):
        super().__init__(Report)

    def get_all_by_user_id(self, user_id: uuid.UUID) -> List[Report]:
        """Get all reports for a user"""
        return self.query().filter_by(user_id=user_id).all()
    
    def get_all_by_user_id_and_type(self, user_id: uuid.UUID, report_type: str) -> List[Report]:
        """Get all reports for a user with specific type"""
        return self.query().filter_by(user_id=user_id, type=report_type).all()

    def get_all_by_user_id_in_range(self, user_id: uuid.UUID, start: datetime, end: datetime, report_type: str = None) -> List[Report]:
        """Get all reports for a user in a given datetime range, optionally filtered by type."""
        query = self.query().filter_by(user_id=user_id)
        query = query.filter(Report.created_at >= start, Report.created_at < end)
        if report_type:
            query = query.filter_by(type=report_type)
        return query.order_by(Report.created_at.asc()).all()

    def get_all_by_month(self, user_id: uuid.UUID, year: int, month: int, report_type: Optional[str] = None) -> List[Report]:
        """Get all reports for a user in a specific month, optionally filtered by type."""
        # 해당 월의 시작일과 다음 달의 시작일을 계산
        start_date = datetime(year, month, 1)
        if month == 12:
            end_date = datetime(year + 1, 1, 1)
        else:
            end_date = datetime(year, month + 1, 1)

        return self.get_all_by_user_id_in_range(user_id, start_date, end_date, report_type)

    def create(self, **kwargs) -> Report:
        """Create a new report"""
        return super().create(**kwargs)