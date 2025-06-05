from datetime import datetime, timedelta, timezone
from uuid import UUID
from typing import Dict
from app.utils.openai_client import get_openai_client, get_completion
from app.utils.time import TimeUtils
from app.utils.prompt.reports.weekly_report_prompts import (
    WEEKLY_REPORT_PROMPT,
    WEEKLY_REPORT_SCRIPT_PROMPT
)

class GenerateWeeklyReport():
    def _call_llm(self, messages: list, error_response: str) -> str:
        """LLM 호출 공통 로직"""
        try:
            client = get_openai_client()
            response = get_completion(client, messages)
            
            if not response:
                return error_response
                
            return response
            
        except Exception as e:
            print(f"[ERROR] LLM 호출 실패:", e)
            return error_response

    def generate_weekly_report(self, user_id, tz):
        """주간 리포트 생성"""
        from .summarize_weekly_report import SummarizeWeeklyReport
        self.summarizer = SummarizeWeeklyReport()
        
        today = datetime.now(tz).strftime("%Y-%m-%d")

        # 1. 주간 성과 요약
        achievements = self.summarizer.summarize_weekly_achievements(user_id, tz)
        
        # 2. 주간 대화/관심사 요약
        conversations = self.summarizer.summarize_weekly_conversations(user_id, tz)
        
        # 3. 주간 인사이트 요약
        insights = self.summarizer.summarize_weekly_articles(user_id, tz)
        
        # 4. 다음 주 할일
        next_tasks = self.summarizer.summarize_next_week_tasks(user_id, tz)

        # 섹션 결합
        sections = f"{achievements}\n\n{conversations}\n\n{insights}\n\n{next_tasks}"

        # 프롬프트 구성 및 LLM 호출
        prompt = WEEKLY_REPORT_PROMPT.format(today=today, sections=sections)
        messages = [
            {"role": "system", "content": "아래 프롬프트에 따라 Weekly Report 마크다운을 생성해줘. 반드시 예시 구조와 순서를 지켜야 해."},
            {"role": "user", "content": prompt}
        ]

        error_response = f"# Weekly Report – {today}\n(데이터 없음)"
        return self._call_llm(messages, error_response)

    def generate_weekly_report_script(self, user_id, markdown=None, tz=None):
        """주간 리포트 브리핑 스크립트 생성"""
        if tz is None:
            tz = TimeUtils.get_timezone("UTC")
        if markdown is None:
            markdown = self.generate_weekly_report(user_id, tz)
            
        now = datetime.now(tz)
        today = now.strftime("%m-%d")
        now_time = now.strftime("%H:%M")
        
        prompt = WEEKLY_REPORT_SCRIPT_PROMPT.format(today=today, now_time=now_time, markdown=markdown)
        
        messages = [
            {"role": "system", "content": "아래 프롬프트에 따라 Weekly Report 브리핑 스크립트를 생성해줘. 반드시 예시 구조와 어조를 지켜야 해."},
            {"role": "user", "content": prompt}
        ]
        
        error_response = f"Weekly Report 브리핑 스크립트 생성이 실패했습니다. 다음 안내가 필요하시면 말씀해주세요."
        return self._call_llm(messages, error_response)
    
    def get_monthly_stats(self, user_id: UUID, tz: timezone) -> Dict:
        """월간 통계 데이터"""
        from app.services.schedule_service import ScheduleService
        self.schedule_service = ScheduleService()
        
        month_start, month_end = TimeUtils.get_month_range(tz)
        total_schedules = self.schedule_service.schedule_dao.get_schedules_count_by_date_range(
            user_id, month_start, month_end
        )
        completed_schedules = self.schedule_service.schedule_dao.get_schedules_count_by_date_range(
            user_id, month_start, month_end, status='done'
        )
        return {
            'total': total_schedules,
            'completed': completed_schedules,
            'completion_rate': completed_schedules / total_schedules if total_schedules > 0 else 0
        }