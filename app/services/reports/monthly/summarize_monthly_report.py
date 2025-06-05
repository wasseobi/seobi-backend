from typing import Dict, List, Any
from uuid import UUID
from datetime import datetime

from app.utils.time import TimeUtils
from app.utils.prompt.monthly_report_prompts import (
    MONTHLY_ACHIEVEMENTS_PROMPT,
    WEEKLY_TRENDS_PROMPT,
    INTEREST_TRENDS_PROMPT,
    NEXT_MONTH_GOALS_PROMPT
)
from ..summarize_report import SummarizeReport


class SummarizeMonthlyReport(SummarizeReport):
    def summarize_monthly_achievements(self, user_id: UUID, tz) -> str:
        """월간 일정 성과를 요약"""
        from app.services.reports.monthly.get_monthly_report import GetMonthlyReport
        monthly_report_getter = GetMonthlyReport()

        schedules = monthly_report_getter.get_monthly_schedules(user_id, tz)
        patterns = monthly_report_getter.analyze_schedule_patterns(
            schedules["all_schedules"])

        # 요일별 분포를 읽기 쉽게 변환
        days = ["월", "화", "수", "목", "금", "토", "일"]
        day_dist = "\n".join(
            [f"{days[day]}: {count}건" for day, count in patterns["day_distribution"].items()])

        # 시간대별 분포를 4시간 단위로 그룹화
        hour_groups = {"새벽(0-5시)": 0, "오전(6-11시)": 0,
                       "오후(12-17시)": 0, "저녁(18-23시)": 0}
        for hour, count in patterns["hour_distribution"].items():
            if 0 <= hour <= 5:
                hour_groups["새벽(0-5시)"] += count
            elif 6 <= hour <= 11:
                hour_groups["오전(6-11시)"] += count
            elif 12 <= hour <= 17:
                hour_groups["오후(12-17시)"] += count
            else:
                hour_groups["저녁(18-23시)"] += count
        hour_dist = "\n".join(
            [f"{time}: {count}건" for time, count in hour_groups.items()])

        prompt = MONTHLY_ACHIEVEMENTS_PROMPT.format(
            year=patterns["year"],
            month=patterns["month"],
            total_schedules=patterns["total_count"],
            completed_schedules=patterns["completed_count"],
            completion_rate=round(patterns["completion_rate"] * 100, 1),
            day_distribution=day_dist,
            hour_distribution=hour_dist
        )

        return self._call_llm(prompt)

    def summarize_weekly_trends(self, user_id: UUID, tz) -> str:
        """주차별 대화 흐름을 요약"""
        from app.services.reports.monthly.get_monthly_report import GetMonthlyReport
        monthly_report_getter = GetMonthlyReport()

        weekly_reports = monthly_report_getter.get_weekly_reports(user_id, tz)

        # 주차별 요약을 모음
        weekly_summaries = []
        for report in weekly_reports:
            week_num = report.created_at.isocalendar()[1]
            summary = f"{week_num}주차:\n{report.content}\n"
            weekly_summaries.append(summary)

        prompt = WEEKLY_TRENDS_PROMPT.format(
            year=weekly_reports[0].created_at.year if weekly_reports else None,
            month=weekly_reports[0].created_at.month if weekly_reports else None,
            weekly_summaries="\n".join(weekly_summaries)
        )

        return self._call_llm(prompt)

    def summarize_interest_trends(self, user_id: UUID, tz) -> str:
        """관심사 및 인사이트 트렌드를 요약"""
        from app.services.reports.monthly.get_monthly_report import GetMonthlyReport
        monthly_report_getter = GetMonthlyReport()

        monthly_interests = monthly_report_getter.get_monthly_interests(
            user_id, tz)

        # 관심사와 인사이트를 문자열로 변환
        interests_str = "\n".join([f"- {interest.name}: {interest.description}"
                                   for interest in monthly_interests["interests"]])
        insights_str = "\n".join([f"- {insight.title}: {insight.content}"
                                  for insight in monthly_interests["insights"]])

        start_date, _ = TimeUtils.get_month_range(tz)
        prompt = INTEREST_TRENDS_PROMPT.format(
            year=start_date.year,
            month=start_date.month,
            interests=interests_str,
            insights=insights_str
        )

        return self._call_llm(prompt)

    def suggest_next_month_goals(self, user_id: UUID, achievements: str, interests: List[str], ongoing_schedules: List[str]) -> str:
        """다음달 목표와 일정을 제안"""
        prompt = NEXT_MONTH_GOALS_PROMPT.format(
            year=datetime.now().year,
            month=datetime.now().month,
            achievements=achievements,
            interests="\n".join([f"- {interest}" for interest in interests]),
            ongoing_schedules="\n".join(
                [f"- {schedule}" for schedule in ongoing_schedules])
        )

        return self._call_llm(prompt)
