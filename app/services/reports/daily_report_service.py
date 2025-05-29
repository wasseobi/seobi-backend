import uuid
from datetime import datetime, timedelta, timezone
from app.services.session_service import SessionService
from app.services.schedule_service import ScheduleService
from app.services.insight_article_service import InsightArticleService
from app.utils.openai_client import get_openai_client, get_completion
from app.utils.prompt.reports.daily_report_prompts import (
    SCHEDULES_MARKDOWN_PROMPT,
    SESSIONS_MARKDOWN_PROMPT,
    ARTICLES_MARKDOWN_PROMPT,
    DAILY_REPORT_MARKDOWN_PROMPT,
    DAILY_REPORT_BRIEFING_PROMPT,
)
import json

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

    def _get_tomorrow_range(self, tz=KST):
        now = datetime.now(tz)
        start_of_today = now.replace(hour=0, minute=0, second=0, microsecond=0)
        start_of_tomorrow = start_of_today + timedelta(days=1)
        start_of_day_after = start_of_today + timedelta(days=2)
        return start_of_tomorrow.astimezone(timezone.utc), start_of_day_after.astimezone(timezone.utc)


    def get_today_schedules_done(self, user_id: uuid.UUID, tz=KST):
        start, end = self._get_today_range(tz)
        schedules = [schedule for schedule in self.schedule_service.dao.get_user_schedules(user_id)
                     if schedule.start_at >= start and schedule.start_at < end and schedule.status == 'done']
        return [
            {
                "id": str(schedule.id),
                "title": schedule.title,
                "repeat": getattr(schedule, 'repeat', None),
                "start_at": to_local(schedule.start_at, tz),
                "finish_at": to_local(schedule.finish_at, tz),
                "location": getattr(schedule, 'location', None),
                "memo": schedule.memo,
                "status": schedule.status
            }
            for schedule in schedules
        ]

    def get_today_schedules_undone(self, user_id: uuid.UUID, tz=KST):
        start, end = self._get_today_range(tz)
        schedules = [schedule for schedule in self.schedule_service.dao.get_user_schedules(user_id)
                     if schedule.start_at >= start and schedule.start_at < end and schedule.status == 'undone']
        return [
            {
                "id": str(schedule.id),
                "title": schedule.title,
                "repeat": getattr(schedule, 'repeat', None),
                "start_at": to_local(schedule.start_at, tz),
                "finish_at": to_local(schedule.finish_at, tz),
                "location": getattr(schedule, 'location', None),
                "memo": schedule.memo,
                "status": schedule.status
            }
            for schedule in schedules
        ]

    def get_tomorrow_schedules(self, user_id: uuid.UUID, tz=KST):
        start, end = self._get_tomorrow_range(tz)
        schedules = [schedule for schedule in self.schedule_service.dao.get_user_schedules(user_id)
                     if schedule.start_at >= start and schedule.start_at < end]
        return [
            {
                "id": str(schedule.id),
                "title": schedule.title,
                "repeat": getattr(schedule, 'repeat', None),
                "start_at": to_local(schedule.start_at, tz),
                "finish_at": to_local(schedule.finish_at, tz),
                "location": getattr(schedule, 'location', None),
                "memo": schedule.memo,
            }
            for schedule in schedules
        ]


    def get_today_sessions(self, user_id: uuid.UUID, tz=KST):
        start, end = self._get_today_range(tz)
        sessions = [session for session in self.session_service.dao.get_user_sessions(user_id)
                    if session.start_at >= start and session.start_at < end]
        return [
            {
                "id": str(session.id),
                "title": session.title,
                "description": session.description,
                "start_at": to_local(session.start_at, tz),
                "finish_at": to_local(session.finish_at, tz)
            }
            for session in sessions
        ]

    def get_today_articles(self, user_id: uuid.UUID, tz=KST):
        start, end = self._get_today_range(tz)
        articles = [article for article in self.article_service.insight_article_dao.get_user_articles(user_id)
                    if article.created_at >= start and article.created_at < end]
        return [
            {
                "id": str(article.id),
                "title": article.title,
                "tag": article.tags,
                "created_at": to_local(article.created_at, tz)
            }
            for article in articles
        ]


    # max_retries - 재시도는 랭그래프로 처리해도 좋을 거 같음

    def summarize_schedules_done_markdown(self, user_id, tz=KST, max_retries=2):
        schedules = self.get_today_schedules_done(user_id, tz)
        count = len(schedules)
        schedules_json = json.dumps(schedules, ensure_ascii=False)
        prompt = SCHEDULES_MARKDOWN_PROMPT.format(header="완료한 일정", count=count)
        client = get_openai_client()
        messages = [
            {"role": "system", "content": "아래 프롬프트에 따라 마크다운 요약을 생성해줘."},
            {"role": "user", "content": prompt + "\n[SCHEDULES_DONE] " + schedules_json}
        ]
        response = None
        for attempt in range(max_retries + 1):
            try:
                response = get_completion(client, messages)
                if response is not None and response.strip() != f"## 완료한 일정 (총 {count}건)":
                    break
            except Exception as e:
                print(f"[WARNING] LLM 호출 실패 (attempt {attempt+1}):", e)
        if response is None or response.strip() == f"## 완료한 일정 (총 {count}건)":
            print(f"[WARNING] LLM 응답이 None이거나 헤더만 반환됨. (count={count})")
            return f"## 완료한 일정 (총 {count}건)"
        return response

    def summarize_schedules_undone_markdown(self, user_id, tz=KST, max_retries=2):
        schedules = self.get_today_schedules_undone(user_id, tz)
        count = len(schedules)
        schedules_json = json.dumps(schedules, ensure_ascii=False)
        # 프롬프트를 더 간결하고 명확하게 개선
        prompt = SCHEDULES_MARKDOWN_PROMPT.format(header="미완료 일정", count=count)
        client = get_openai_client()
        messages = [
            {"role": "system", "content": "아래 프롬프트에 따라 마크다운 요약을 생성해줘."},
            {"role": "user", "content": prompt + "\n[SCHEDULES_UNDONE] " + schedules_json}
        ]
        response = None
        for attempt in range(max_retries + 1):
            try:
                response = get_completion(client, messages)
                if response is not None and response.strip() != f"## 미완료 일정 (총 {count}건)":
                    break
            except Exception as e:
                print(f"[WARNING] LLM 호출 실패 (attempt {attempt+1}):", e)
        if response is None or response.strip() == f"## 미완료 일정 (총 {count}건)":
            print(f"[WARNING] LLM 응답이 None이거나 헤더만 반환됨. (count={count})")
            return f"## 미완료 일정 (총 {count}건)"
        return response

    def summarize_tomorrow_schedules_markdown(self, user_id, tz=KST, max_retries=2):
        schedules = self.get_tomorrow_schedules(user_id, tz)
        count = len(schedules)
        schedules_json = json.dumps(schedules, ensure_ascii=False)
        prompt = SCHEDULES_MARKDOWN_PROMPT.format(header="내일 일정", count=count)
        client = get_openai_client()
        messages = [
            {"role": "system", "content": "아래 프롬프트에 따라 마크다운 요약을 생성해줘."},
            {"role": "user", "content": prompt + "\n[TOMORROW_SCHEDULES] " + schedules_json}
        ]
        response = None
        for attempt in range(max_retries + 1):
            try:
                response = get_completion(client, messages)
                if response is not None and response.strip() != f"## 내일 일정 (총 {count}건)":
                    break
            except Exception as e:
                print(f"[WARNING] LLM 호출 실패 (attempt {attempt+1}):", e)
        if response is None or response.strip() == f"## 내일 일정 (총 {count}건)":
            print(f"[WARNING] LLM 응답이 None이거나 헤더만 반환됨. (count={count})")
            return f"## 내일 일정 (총 {count}건)"
        return response

    def summarize_sessions_markdown(self, user_id, tz=KST, max_retries=2):
        sessions = self.get_today_sessions(user_id, tz)
        count = len(sessions)
        sessions_json = json.dumps(sessions, ensure_ascii=False)
        prompt = SESSIONS_MARKDOWN_PROMPT.format(count=count)
        client = get_openai_client()
        messages = [
            {"role": "system", "content": "아래 프롬프트에 따라 마크다운 요약을 생성해줘."},
            {"role": "user", "content": prompt + "\n[SESSIONS] " + sessions_json}
        ]
        response = None
        for attempt in range(max_retries + 1):
            try:
                response = get_completion(client, messages)
                if response is not None and response.strip() != f"## 대화 세션 요약 (총 {count}건)":
                    break
            except Exception as e:
                print(f"[WARNING] LLM 호출 실패 (attempt {attempt+1}):", e)
        if response is None or response.strip() == f"## 대화 세션 요약 (총 {count}건)":
            print(f"[WARNING] LLM 응답이 None이거나 헤더만 반환됨. (count={count})")
            return f"## 대화 세션 요약 (총 {count}건)"
        return response

    def summarize_today_articles_markdown(self, user_id, tz=KST, max_retries=2):
        articles = self.get_today_articles(user_id, tz)
        count = len(articles)
        articles_json = json.dumps(articles, ensure_ascii=False)
        prompt = ARTICLES_MARKDOWN_PROMPT.format(count=count)
        client = get_openai_client()
        messages = [
            {"role": "system", "content": "아래 프롬프트에 따라 마크다운 요약을 생성해줘."},
            {"role": "user", "content": prompt + "\n[ARTICLES] " + articles_json}
        ]
        response = None
        for attempt in range(max_retries + 1):
            try:
                response = get_completion(client, messages)
                if response is not None and response.strip() != f"## 오늘의 아티클 (총 {count}건)":
                    break
            except Exception as e:
                print(f"[WARNING] LLM 호출 실패 (attempt {attempt+1}):", e)
        if response is None or response.strip() == f"## 오늘의 아티클 (총 {count}건)":
            print(f"[WARNING] LLM 응답이 None이거나 헤더만 반환됨. (count={count})")
            return f"## 오늘의 아티클 (총 {count}건)"
        return response

    def generate_daily_report_markdown(self, user_id, user_name, tz=KST, max_retries=2):
        from datetime import datetime
        today = datetime.now(tz).strftime("%Y-%m-%d")
        done = self.summarize_schedules_done_markdown(user_id, tz, max_retries)
        undone = self.summarize_schedules_undone_markdown(user_id, tz, max_retries)
        tomorrow = self.summarize_tomorrow_schedules_markdown(user_id, tz, max_retries)
        sessions = self.summarize_sessions_markdown(user_id, tz, max_retries)
        articles = self.summarize_today_articles_markdown(user_id, tz, max_retries)
        sections = f"{done}\n\n{undone}\n\n{tomorrow}\n\n{sessions}\n\n{articles}"
        prompt = DAILY_REPORT_MARKDOWN_PROMPT.format(today=today, sections=sections)
        client = get_openai_client()
        messages = [
            {"role": "system", "content": "아래 프롬프트에 따라 Daily Report 마크다운을 생성해줘. 반드시 예시 구조와 순서를 지켜야 해."},
            {"role": "user", "content": prompt}
        ]
        response = None
        for attempt in range(max_retries + 1):
            try:
                response = get_completion(client, messages)
                if response and response.strip().startswith(f"# Daily Report – {today}"):
                    break
            except Exception as e:
                print(f"[WARNING] Daily Report 마크다운 LLM 호출 실패 (attempt {attempt+1}):", e)
        if not response:
            print("[WARNING] Daily Report 마크다운 생성 실패. 빈 마크다운 반환.")
            return f"# Daily Report – {today}\n(데이터 없음)"
        return response

    def generate_briefing_script(self, user_id, user_name, markdown=None, tz=KST, max_retries=2):
        # 만약 markdown이 None이면, 자동으로 generate_daily_report_markdown을 호출해서 사용
        if markdown is None:
            markdown = self.generate_daily_report_markdown(user_id, user_name, tz, max_retries)
        now = datetime.now(tz)
        today = now.strftime("%m-%d")
        now_time = now.strftime("%H:%M")
        prompt = DAILY_REPORT_BRIEFING_PROMPT.format(user_name=user_name, today=today, now_time=now_time, markdown=markdown)
        client = get_openai_client()
        messages = [
            {"role": "system", "content": "아래 프롬프트에 따라 Daily Report 브리핑 스크립트를 생성해줘. 반드시 예시 구조와 어조를 지켜야 해."},
            {"role": "user", "content": prompt}
        ]
        response = None
        for attempt in range(max_retries + 1):
            try:
                response = get_completion(client, messages)
                if response and response.strip().startswith(f"안녕하세요. {user_name} 님의 {today} {now_time}"):
                    break
            except Exception as e:
                print(f"[WARNING] 브리핑 스크립트 LLM 호출 실패 (attempt {attempt+1}):", e)
        if not response:
            print("[WARNING] Daily Report 브리핑 스크립트 생성 실패. 빈 스크립트 반환.")
            return f"Daily Report 브리핑 스크립트 생성이 실패했습니다다. 다음 안내가 필요하시면 말씀해주세요."
        return response

    def generate_daily_report_json(self, user_id, user_name, tz=KST, max_retries=2):
        markdown = self.generate_daily_report_markdown(user_id, user_name, tz, max_retries)
        script = self.generate_briefing_script(user_id, user_name, markdown, tz, max_retries)
        return {
            "text": markdown,
            "script": script
        }