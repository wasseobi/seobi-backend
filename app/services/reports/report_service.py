from typing import Any, Dict
from app.dao.report_dao import ReportDAO
from app.services.reports.generate_report_service import GenerateReportService
from app.services.reports.generate_report_service import get_timezone

class ReportService:
    def __init__(self):
        self.report_dao = ReportDAO()
        self.generator = GenerateReportService()

    def _serialize_report(self, report: Any) -> Dict[str, Any]:
        """Serialize Report model instance for API response"""
        return {
            'id': str(report.id),
            'user_id': str(report.user_id),
            'schedule_id': str(report.schedule_id),
            'content': report.content,
            'type': report.type
        }

    def get_user_reports(self, user_id):
        reports = self.report_dao.get_by_user(user_id)
        return [self._serialize_report(r) for r in reports]

    def get_report(self, report_id):
        report = self.report_dao.get(report_id)
        return self._serialize_report(report) if report else None

    def create_report(self, data):
        report = self.report_dao.create(**data)
        return self._serialize_report(report)

    def delete_report(self, report_id):
        return self.report_dao.delete(report_id)

    def generate_and_create_report(self, user_id, schedule_id, user_name, tz_str, report_type='daily', max_retries=2):
        tz = get_timezone(tz_str)
        report_data = self.generator.generate_report(user_id, user_name, tz, report_type, max_retries)
        db_data = {
            "user_id": user_id,
            "schedule_id": schedule_id,
            "content": {
                "text": report_data["text"],
                "script": report_data["script"]
            },
            "type": report_type
        }
        report = self.create_report(db_data)
        return report