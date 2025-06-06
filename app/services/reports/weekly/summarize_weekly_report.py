from datetime import timezone
import json
from uuid import UUID
from app.utils.prompt.reports.weekly_report_prompts import (
    WEEKLY_ACHIEVEMENTS_PROMPT,
    WEEKLY_CONVERSATION_PROMPT,
    WEEKLY_ARTICLES_PROMPT,
    WEEKLY_NEXT_TASKS_PROMPT
)
from .get_weekly_report import GetWeeklyReport
from ..summarize_report import SummarizeReport
from app.utils.time import TimeUtils

class SummarizeWeeklyReport(SummarizeReport):
    def __init__(self):
        super().__init__()
        self.get_report_service = GetWeeklyReport()

    def summarize_weekly_achievements(self, user_id: UUID, tz: timezone) -> str:
        """주간 성과 요약"""
        from app.services.reports.report_service import ReportService
        self.report_service = ReportService()
        self.report_service = ReportService()
        week_start, week_end = TimeUtils.get_week_range(tz)
        schedules = self.schedule_service.get_schedule_by_date_range_status(
            user_id, start=week_start, end=week_end, status='done')
        daily_reports = self.report_service.get_reports_by_date_range(user_id, start=week_start, end=week_end, report_type='daily')

        schedule_count = len(schedules)
        report_count = len(daily_reports)

        data = {
            "schedules": schedules,
            "daily_reports": daily_reports
        }
        data_json = json.dumps(data, ensure_ascii=False)

        prompt = WEEKLY_ACHIEVEMENTS_PROMPT.format(
            schedule_count=schedule_count,
            report_count=report_count,
            data=data_json
        )

        messages = self._create_messages(
            "주간 성과를 요약하여 마크다운으로 작성해주세요.",
            prompt,
            data_json
        )

        return self._call_llm(messages, "주간 성과 요약")

    def summarize_weekly_conversations(self, user_id: UUID, tz: timezone) -> str:
        """주간 대화/관심사 요약"""
        daily_reports = self.get_report_service.get_weekly_daily_reports(
            user_id, tz)
        interests = self.get_report_service.get_weekly_interests(user_id, tz)

        interests_json = json.dumps(interests, ensure_ascii=False)
        conversations_json = json.dumps(daily_reports, ensure_ascii=False)

        prompt = WEEKLY_CONVERSATION_PROMPT.format(
            interests_data=interests_json,
            conversations_data=conversations_json
        )

        messages = self._create_messages(
            "주간 대화 내용과 관심사를 요약하여 마크다운으로 작성해주세요.",
            prompt
        )

        return self._call_llm(messages, "주간 대화/관심사 요약")

    def summarize_weekly_articles(self, user_id: UUID, tz: timezone) -> str:
        """주간 아티클 요약"""
        articles = self.get_report_service.get_weekly_articles(user_id, tz)
        count = len(articles)
        articles_json = json.dumps(articles, ensure_ascii=False)

        prompt = WEEKLY_ARTICLES_PROMPT.format(count=count)
        messages = self._create_messages(
            "이번 주의 인사이트 아티클을 마크다운으로 요약해주세요.",
            prompt,
            articles_json
        )

        return self._call_llm(messages, "금주의 아티클", count)

    def summarize_next_week_tasks(self, user_id: UUID, tz: timezone) -> str:
        """다음 주 할일 요약"""
        tasks = self.get_report_service.get_next_week_tasks(user_id, tz)
        count = len(tasks)
        tasks_json = json.dumps(tasks, ensure_ascii=False)

        prompt = WEEKLY_NEXT_TASKS_PROMPT.format(
            count=count,
            tasks_data=tasks_json
        )

        messages = self._create_messages(
        "다음 주 예정된 일정들을 마크다운으로 요약해주세요.",
        prompt,
        tasks_json
        )

        return self._call_llm(messages, "다음 주 할 일", count)
