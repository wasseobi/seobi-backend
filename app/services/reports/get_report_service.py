import uuid
from datetime import datetime, timedelta, timezone
from app.services.session_service import SessionService
from app.services.schedule_service import ScheduleService
from app.services.insight_article_service import InsightArticleService
from app.utils.time import TimeUtils


class GetReportService:
    def __init__(self):
        self.session_service = SessionService()
        self.schedule_service = ScheduleService()
        self.article_service = InsightArticleService()

    def get_schedules(self, user_id: uuid.UUID, tz, when='today', status=None):
        if when == 'today':
            start, end = TimeUtils.get_today_range(tz)
        elif when == 'tomorrow':
            start, end = TimeUtils.get_tomorrow_range(tz)
        else:
            raise ValueError("when은 'today' 또는 'tomorrow'만 지원합니다.")

        # status 파라미터에 따라 완료/미완료/전체 분기
        if status == 'done':
            status_filter = 'done'
        elif status == 'undone':
            status_filter = 'undone'
        elif status is None:
            status_filter = None
        else:
            raise ValueError("status는 'done', 'undone', None만 지원합니다.")

        schedules = self.schedule_service.schedule_dao.get_all_by_user_id_in_range(user_id, start, end, status=status_filter)
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

    def get_today_sessions(self, user_id: uuid.UUID, tz):
        start, end = TimeUtils.get_today_range(tz)
        sessions = [session for session in self.session_service.session_dao.get_user_sessions(user_id)
                    if session.start_at >= start and session.start_at < end]
        return [
            {
                "id": str(session.id),
                "title": session.title,
                "description": session.description,
                "start_at": TimeUtils.to_local(session.start_at, tz),
                "finish_at": TimeUtils.to_local(session.finish_at, tz)
            }
            for session in sessions
        ]

    def get_today_articles(self, user_id: uuid.UUID, tz):
        start, end = TimeUtils.get_today_range(tz)
        articles = [article for article in self.article_service.insight_article_dao.get_all_by_user_id(user_id)
                    if article.created_at >= start and article.created_at < end]
        return [
            {
                "id": str(article.id),
                "title": article.title,
                "tag": article.tags,
                "created_at": TimeUtils.to_local(article.created_at, tz)
            }
            for article in articles
        ]
