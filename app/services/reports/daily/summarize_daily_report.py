import json
from app.utils.prompt.reports.daily_report_prompts import (
    DAILY_SCHEDULES_PROMPT,
    DAILY_SESSIONS_PROMPT,
    TODAY_ARTICLES_PROMPT,
)
from ..summarize_report import SummarizeReport
from .get_daily_report import GetDailyReport

class SummarizeDailyReport(SummarizeReport):
    def __init__(self):
        super().__init__()
        self.get_report_service = GetDailyReport()

    def summarize_daily_schedules(self, user_id, tz, when='today', status=None):
        schedules = self.get_report_service.get_today_schedules(
            user_id, tz, when=when, status=status)
        count = len(schedules)

        if when == 'tomorrow':
            header = "내일 일정"
        elif status == 'done':
            header = "완료한 일정"
        elif status == 'undone':
            header = "미완료 일정"
        else:
            raise ValueError("지원하지 않는 일정 유형입니다.")

        prompt = DAILY_SCHEDULES_PROMPT.format(header=header, count=count)
        schedules_json = json.dumps(schedules, ensure_ascii=False)
        
        messages = self._create_messages(
                    "아래 프롬프트에 따라 마크다운 요약을 생성해줘.",
                    prompt,
                    schedules_json
                )

        return self._call_llm(messages, header, count)

    def summarize_daily_sessions(self, user_id, tz):
        sessions = self.get_report_service.get_today_sessions(user_id, tz)
        count = len(sessions)
        sessions_json = json.dumps(sessions, ensure_ascii=False)

        prompt = DAILY_SESSIONS_PROMPT.format(count=count)
        messages = self._create_messages(
            "아래 프롬프트에 따라 마크다운 요약을 생성해줘.",
            prompt,
            sessions_json
        )

        return self._call_llm(messages, "대화 세션 요약", count)

    def summarize_daily_articles(self, user_id, tz):
        articles = self.get_report_service.get_today_articles(user_id, tz)
        count = len(articles)
        articles_json = json.dumps(articles, ensure_ascii=False)

        prompt = TODAY_ARTICLES_PROMPT.format(count=count)
        messages = self._create_messages(
            "아래 프롬프트에 따라 마크다운 요약을 생성해줘.",
            prompt,
            articles_json
        )

        return self._call_llm(messages, "오늘의 아티클", count)
