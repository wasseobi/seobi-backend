from typing import Dict, Any
from uuid import UUID

from app.utils.prompt.monthly_report_prompts import (
    MONTHLY_REPORT_PROMPT,
    MONTHLY_SCRIPT_PROMPT
)
from app.services.reports.monthly.summarize_monthly_report import SummarizeMonthlyReport
from app.services.interest_service import InterestService
from app.services.schedule_service import ScheduleService
from app.utils.time import TimeUtils


class GenerateMonthlyReport():
    def __init__(self):
        self.summarizer = SummarizeMonthlyReport()
        self.interest_service = InterestService()
        self.schedule_service = ScheduleService()

    def generate_monthly_report(self, user_id: UUID, tz) -> str:
        """월간 리포트 생성"""
        # 각 섹션별 요약 생성
        monthly_achievements = self.summarizer.summarize_monthly_achievements(
            user_id, tz)
        weekly_trends = self.summarizer.summarize_weekly_trends(user_id, tz)
        interest_trends = self.summarizer.summarize_interest_trends(
            user_id, tz)
        start_date, end_date = TimeUtils.get_month_range(tz)

        # 다음달 목표 제안을 위한 데이터 준비
        interests = self.interest_service.interest_dao.get_all_by_user_id_date_range(
            user_id, start_date, end_date)
        ongoing_schedules = self.schedule_service.get_all_by_ongoing(
            user_id, end_date)
        next_month_goals = self.summarizer.suggest_next_month_goals(
            user_id, monthly_achievements, interests, ongoing_schedules
        )

        # 최종 리포트 생성
        start_date, _ = TimeUtils.get_month_range(tz)
        report = MONTHLY_REPORT_PROMPT.format(
            year=start_date.year,
            month=start_date.month,
            monthly_achievements=monthly_achievements,
            weekly_trends=weekly_trends,
            interest_trends=interest_trends,
            next_month_goals=next_month_goals
        )

        return report

    def generate_monthly_report_script(self, user_id: UUID, markdown: str, tz) -> str:
        """월간 리포트 스크립트 생성"""
        # 마크다운 리포트를 섹션별로 분리
        sections = self._split_markdown_to_sections(markdown)

        # 스크립트 생성
        start_date, _ = TimeUtils.get_month_range(tz)
        script = MONTHLY_SCRIPT_PROMPT.format(
            year=start_date.year,
            month=start_date.month,
            monthly_achievements_script=sections["monthly_achievements"],
            weekly_trends_script=sections["weekly_trends"],
            interest_trends_script=sections["interest_trends"],
            next_month_goals_script=sections["next_month_goals"]
        )

        return script

    def _split_markdown_to_sections(self, markdown: str) -> Dict[str, str]:
        """마크다운 리포트를 섹션별로 분리"""
        sections = {
            "monthly_achievements": "",
            "weekly_trends": "",
            "interest_trends": "",
            "next_month_goals": ""
        }

        # TODO (Jooeun-report): 마크다운 텍스트를 섹션별로 분리하는 로직 구현
        # 현재는 간단한 구현만 포함
        # 나중에 먼슬리 하면 수정...
        lines = markdown.split("\n")
        current_section = None

        for line in lines:
            if "월간 일정 성과" in line:
                current_section = "monthly_achievements"
            elif "주차별 대화 흐름" in line:
                current_section = "weekly_trends"
            elif "관심사 및 인사이트" in line:
                current_section = "interest_trends"
            elif "다음 달 목표" in line:
                current_section = "next_month_goals"
            elif current_section:
                sections[current_section] += line + "\n"

        return sections
