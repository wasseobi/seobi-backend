import uuid
from datetime import datetime, timedelta, timezone
from app.utils.time import TimeUtils


class GetWeeklyReport():
    def get_weekly_daily_reports(self, user_id: uuid.UUID, tz: timezone) -> list:
        """주간 데일리 리포트 조회"""
        from app.services.reports.report_service import ReportService
        self.report_service = ReportService()

        week_start, week_end = TimeUtils.get_week_range(tz)
        reports = self.report_service.get_reports_by_date_range(
            user_id, start=week_start, end=week_end, report_type='daily'
        )
        return [
            {
                "id": str(report.id),
                "content": report.content,
                "created_at": TimeUtils.to_local(report.created_at, tz),
                "type": report.type
            }
            for report in reports
        ]

    def get_weekly_interests(self, user_id: uuid.UUID, tz: timezone) -> list:
        """주간 관심사 조회"""
        from app.services.interest_service import InterestService
        self.interest_service = InterestService()

        week_start, week_end = TimeUtils.get_week_range(tz)
        interests = self.interest_service.get_all_by_user_id_date_range(
            user_id, start=week_start, end=week_end
        )
        return [
            {
                "id": str(interest.id),
                "keyword": interest.keyword,
                "weight": interest.weight,
                "created_at": TimeUtils.to_local(interest.created_at, tz)
            }
            for interest in interests
        ]

    def get_weekly_articles(self, user_id: uuid.UUID, tz: timezone) -> list:
        """주간 아티클 조회"""
        from app.services.insight_article_service import InsightArticleService
        self.article_service = InsightArticleService()

        week_start, week_end = TimeUtils.get_week_range(tz)
        articles = self.article_service.get_user_articles_in_range(
            user_id, week_start, week_end)

        return [
            {
                "id": str(article.id),
                "title": article.title,
                "tag": article.tags,
                "created_at": TimeUtils.to_local(article.created_at, tz)
            }
            for article in articles
        ]

    def get_next_week_tasks(self, user_id: uuid.UUID, tz: timezone) -> list:
        """다음 주 미완료 일정 조회"""
        from app.services.schedule_service import ScheduleService
        self.schedule_service = ScheduleService()

        next_week_start, next_week_end = TimeUtils.get_next_week_range(tz)
        schedules = self.schedule_service.get_by_date_range_status(
            user_id, next_week_start, next_week_end, status='undone'
        )
        return [
            {
                "id": str(schedule.id),
                "title": schedule.title,
                "repeat": getattr(schedule, 'repeat', None),
                "start_at": TimeUtils.to_local(schedule.start_at, tz),
                "finish_at": TimeUtils.to_local(schedule.finish_at, tz),
                "location": getattr(schedule, 'location', None),
                "memo": schedule.memo,
                "status": getattr(schedule, 'status', None)
            }
            for schedule in schedules
        ]
