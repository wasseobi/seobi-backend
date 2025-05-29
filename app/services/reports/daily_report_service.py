import uuid
from datetime import datetime, timedelta, timezone
from app.services.session_service import SessionService
from app.services.schedule_service import ScheduleService
from app.services.insight_article_service import InsightArticleService
from app.utils.openai_client import get_openai_client, get_completion

KST = timezone(timedelta(hours=9))

def to_local(dt, tz=KST):
    if dt is None:
        return None
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(tz).isoformat()

class DailyReportService:
    def __init__(self):
        self.session_service = SessionService()
        self.schedule_service = ScheduleService()
        self.article_service = InsightArticleService()

    def _get_today_range(self, tz=KST):
        now = datetime.now(tz)
        start_of_today = now.replace(hour=0, minute=0, second=0, microsecond=0)
        start_of_tomorrow = start_of_today + timedelta(days=1)
        return start_of_today.astimezone(timezone.utc), start_of_tomorrow.astimezone(timezone.utc)

    def collect_today_sessions(self, user_id: uuid.UUID, tz=KST):
        start, end = self._get_today_range(tz)
        sessions = self.session_service.dao.query().filter_by(user_id=user_id) \
            .filter(self.session_service.dao.model.start_at >= start) \
            .filter(self.session_service.dao.model.start_at < end).all()
        return [
            {
                "id": str(s.id),
                "title": s.title,
                "description": s.description,
                "start_at": to_local(s.start_at, tz),
                "finish_at": to_local(s.finish_at, tz)
            }
            for s in sessions
        ]

    def collect_today_schedules(self, user_id: uuid.UUID, tz=KST):
        start, end = self._get_today_range(tz)
        schedules = self.schedule_service.dao.query().filter_by(user_id=user_id) \
            .filter(self.schedule_service.dao.model.start_at >= start) \
            .filter(self.schedule_service.dao.model.start_at < end).all()
        result = []
        for schedule in schedules:
            result.append({
                "id": str(schedule.id),
                "title": schedule.title,
                "repeat": getattr(schedule, 'repeat', None),
                "start_at": to_local(schedule.start_at, tz),
                "finish_at": to_local(schedule.finish_at, tz),
                "location": getattr(schedule, 'location', None),
                "memo": schedule.memo,
                "status": schedule.status
            })
        return result

    def collect_today_articles(self, user_id: uuid.UUID, tz=KST):
        start, end = self._get_today_range(tz)
        articles = self.article_service.insight_article_dao.query().filter_by(user_id=user_id) \
            .filter(self.article_service.insight_article_dao.model.created_at >= start) \
            .filter(self.article_service.insight_article_dao.model.created_at < end).all()
        return [
            {
                "id": str(a.id),
                "title": a.title,
                "content": a.content,
                "created_at": to_local(a.created_at, tz)
            }
            for a in articles
        ]

    def summarize_sessions(self, sessions):
        client = get_openai_client()
        prompt = [
            {"role": "system", "content": "아래 세션 목록을 오늘의 주요 활동 위주로 요약해줘."},
            {"role": "user", "content": str(sessions)}
        ]
        return get_completion(client, prompt)

    def summarize_schedules(self, schedules):
        client = get_openai_client()
        prompt = [
            {"role": "system", "content": "아래 일정 목록을 오늘의 일정 위주로 요약해줘."},
            {"role": "user", "content": str(schedules)}
        ]
        return get_completion(client, prompt)

    def summarize_articles(self, articles):
        client = get_openai_client()
        prompt = [
            {"role": "system", "content": "아래 아티클 목록을 오늘의 주요 인사이트 위주로 요약해줘."},
            {"role": "user", "content": str(articles)}
        ]
        return get_completion(client, prompt)
