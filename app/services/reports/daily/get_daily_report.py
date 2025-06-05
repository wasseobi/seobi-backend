import uuid
from datetime import datetime
from app.utils.time import TimeUtils

class GetDailyReport():
    def get_today_schedules(self, user_id: uuid.UUID, tz, when='today', status=None):
        from app.services.schedule_service import ScheduleService
        self.schedule_service = ScheduleService()

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

        schedules = self.schedule_service.schedule_dao.get_schedules_by_date_range(user_id, start, end, status=status_filter)
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
        from app.services.session_service import SessionService
        self.session_service = SessionService()
        
        start, end = TimeUtils.get_today_range(tz)
        
        all_sessions = self.session_service.get_user_sessions(user_id)
        sessions = []
        
        for session in all_sessions:
            if not session.get('start_at'):
                continue
                
            session_start = datetime.fromisoformat(session['start_at'].replace('Z', '+00:00'))
            if start <= session_start < end:
                finish_at = None
                if session.get('finish_at'):
                    finish_at = TimeUtils.to_local(
                        datetime.fromisoformat(session['finish_at'].replace('Z', '+00:00')), 
                        tz
                    )
                    
                sessions.append({
                    "id": str(session['id']),
                    "title": session['title'],
                    "description": session['description'],
                    "start_at": TimeUtils.to_local(session_start, tz),
                    "finish_at": finish_at
                })
                
        return sessions

    def get_today_articles(self, user_id: uuid.UUID, tz):
        from app.services.insight_article_service import InsightArticleService
        self.article_service = InsightArticleService()

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