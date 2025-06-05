from datetime import datetime
from typing import List, Optional
import uuid
from app.models import Report, db

class ReportDAO:
    def get_by_user(self, user_id):
        return Report.query.filter_by(user_id=user_id).all()

    def get(self, report_id):
        return Report.query.get(report_id)

    def create(self, **kwargs):
        report = Report(**kwargs)
        db.session.add(report)
        db.session.commit()
        return report

    def delete(self, report_id):
        report = self.get(report_id)
        if report:
            db.session.delete(report)
            db.session.commit()
            return True
        return False

    def get_by_user_and_type(self, user_id, report_type):
        return Report.query.filter_by(user_id=user_id, type=report_type).all()

    def get_reports_by_date_range(self, user_id: uuid.UUID, start: datetime, end: datetime, report_type: str = None) -> List[Report]:
        """Get all reports for a user in a given datetime range, optionally filtered by type."""
        query = Report.query.filter_by(user_id=user_id)
        query = query.filter(Report.created_at >= start, Report.created_at < end)
        if report_type:
            query = query.filter_by(type=report_type)
        return query.order_by(Report.created_at.asc()).all()

    def get_reports_by_month(self, user_id: uuid.UUID, year: int, month: int, report_type: Optional[str] = None) -> List[Report]:
        """Get all reports for a user in a specific month, optionally filtered by type."""
        # 해당 월의 시작일과 다음 달의 시작일을 계산
        start_date = datetime(year, month, 1)
        if month == 12:
            end_date = datetime(year + 1, 1, 1)
        else:
            end_date = datetime(year, month + 1, 1)

        return self.get_reports_by_date_range(user_id, start_date, end_date, report_type)

    def get_weekly_reports_in_month(self, user_id: uuid.UUID, year: int, month: int) -> List[Report]:
        """Get all weekly reports for a user in a specific month."""
        return self.get_reports_by_month(user_id, year, month, 'weekly')

    def get_daily_reports_in_month(self, user_id: uuid.UUID, year: int, month: int) -> List[Report]:
        """Get all daily reports for a user in a specific month."""
        return self.get_reports_by_month(user_id, year, month, 'daily')