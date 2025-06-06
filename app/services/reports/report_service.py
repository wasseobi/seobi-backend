from typing import Any, Dict, List, Optional
from uuid import UUID
from datetime import timezone
from app.dao.report_dao import ReportDAO
from app.services.schedule_service import ScheduleService
from app.services.reports.generate_report import GenerateReport
from app.utils.time import TimeUtils


class ReportService:
    def __init__(self):
        self.report_dao = ReportDAO()
        self.generator = GenerateReport()
        self.schedule_service = ScheduleService()

    def _serialize_report(self, report: Any) -> Dict[str, Any]:
        """Serialize Report model instance for API response"""
        return {
            'id': str(report.id),
            'user_id': str(report.user_id),
            'content': report.content,
            'type': report.type
        }

    def get_user_reports(self, user_id):
        reports = self.report_dao.get_all_by_user_id(user_id)
        return [self._serialize_report(r) for r in reports]

    def get_user_type_reports(self, user_id, type):
        reports = self.report_dao.get_all_by_user_id_and_type(user_id, type)
        return [self._serialize_report(r) for r in reports]

    def get_report(self, report_id):
        report = self.report_dao.get_all(report_id)
        return self._serialize_report(report) if report else None

    def get_reports_by_date_range(self, user_id: UUID, start: timezone, end: timezone, report_type: Optional[str] = None) -> List[Dict]:
        """지정된 날짜 범위 내의 리포트 조회"""
        return self.report_dao.get_all_by_user_id_in_range(
            user_id, start, end, report_type=report_type
        )

    def get_reports_month_by_type(self, user_id: UUID, year: int, month: int, report_type: str) -> List[Dict]:
        """특정 연도와 월에 해당하는 리포트 조회"""
        return self.report_dao.get_all_by_month(user_id, year, month, report_type=report_type)

    def create_report(self, data):
        report = self.report_dao.create(**data)
        return self._serialize_report(report)

    def delete_report(self, report_id):
        return self.report_dao.delete(report_id)

    def generate_report(self, user_id, tz_str, report_type):
        """리포트 콘텐츠를 생성합니다."""
        tz = TimeUtils.get_timezone(tz_str)

        if isinstance(user_id, str):
            user_id = UUID(user_id)

        if report_type == 'daily':
            report_data = self.generator.format_report_content(
                user_id, tz, report_type='daily')
        elif report_type == 'weekly':
            report_data = self.generator.format_report_content(
                user_id, tz, report_type='weekly')
        # elif report_type == 'monthly':
        #     report_data = self.generator.format_report_content(user_id, tz, report_type='monthly')

        # report_data가 문자열인 경우를 처리
        if isinstance(report_data, str):
            content = {
                "text": report_data,
                "script": ""
            }
        else:
            content = report_data

        return content

    def save_report(self, user_id, content, report_type):
        """생성된 리포트를 데이터베이스에 저장합니다."""
        if isinstance(user_id, str):
            user_id = UUID(user_id)

        db_data = {
            "user_id": user_id,
            "content": content,
            "type": report_type
        }
        try:
            report = self.create_report(db_data)
            return report
        except Exception as e:
            print(f"Report creation failed: {str(e)}")
            print(f"Attempted data: {db_data}")
            raise
