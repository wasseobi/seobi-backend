from datetime import datetime
from typing import Dict, List, Tuple, Any
from uuid import UUID

from app.models import Report, Schedule
from app.utils.time import TimeUtils

class GetMonthlyReport():
    def get_monthly_schedules(self, user_id: UUID, tz) -> Dict[str, List[Schedule]]:
        """월간 전체 일정과 완료된 일정을 가져옴"""
        from app.services.schedule_service import ScheduleService
        self.schedule_service = ScheduleService()
        
        start_date, end_date = TimeUtils.get_month_range(tz)
        
        # 전체 일정과 완료된 일정을 가져옴
        all_schedules = self.schedule_service.schedule_dao.get_all_by_user_id_in_range(user_id, start_date, end_date)
        completed_schedules = [s for s in all_schedules if s.is_completed]
        
        return {
            "all_schedules": all_schedules,
            "completed_schedules": completed_schedules
        }

    def get_weekly_reports(self, user_id: UUID, tz) -> List[Report]:
        """해당 월의 주간 리포트들을 가져옴"""
        from app.services.reports.report_service import ReportService
        self.report_service = ReportService()
        
        start_date, end_date = TimeUtils.get_month_range(tz)
        year, month = TimeUtils.get_month_of_year(start_date)
        
        return self.report_service.report_dao.get_weekly_reports_in_month(user_id, year, month)

    def get_monthly_interests(self, user_id: UUID, tz) -> Dict[str, List[Any]]:
        """월간 관심사 및 인사이트를 가져옴"""
        from app.services.interest_service import InterestService
        from app.services.insight_article_service import InsightArticleService
        
        self.interest_service = InterestService()
        self.insight_article_service = InsightArticleService()
        
        start_date, end_date = TimeUtils.get_month_range(tz)
        
        # 해당 월의 관심사와 인사이트를 가져옴
        interests = self.interest_service.interest_dao.get_all_by_user_id_date_range(user_id, start_date, end_date)
        insight_articles = self.insight_article_service.insight_article_dao.get_insight_article_by_date_range(user_id, start_date, end_date)
        
        return {
            "interests": interests,
            "insights": insight_articles
        }

    def analyze_schedule_patterns(self, schedules: List[Schedule]) -> Dict[str, Any]:
        """일정 패턴을 분석"""
        total_count = len(schedules)
        completed_count = len([s for s in schedules if s.is_completed])
        
        # 요일별 일정 분포
        day_distribution = {i: 0 for i in range(7)}  # 0: 월요일, 6: 일요일
        for schedule in schedules:
            day = schedule.start_time.weekday()
            day_distribution[day] += 1
            
        # 시간대별 일정 분포
        hour_distribution = {i: 0 for i in range(24)}
        for schedule in schedules:
            hour = schedule.start_time.hour
            hour_distribution[hour] += 1
            
        return {
            "total_count": total_count,
            "completed_count": completed_count,
            "completion_rate": (completed_count / total_count) if total_count > 0 else 0,
            "day_distribution": day_distribution,
            "hour_distribution": hour_distribution
        }
