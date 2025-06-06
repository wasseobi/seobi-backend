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

    def get_week_info(self, now):
        """월과 주차 정보 계산"""
        month = now.month
        
        # 이번 달의 첫 날
        first_day = now.replace(day=1)
        # 첫 주의 월요일부터 시작
        while first_day.weekday() != 0:  # 0: 월요일
            first_day -= timedelta(days=1)
            
        # 현재 날짜가 몇 번째 주인지 계산
        week = ((now - first_day).days // 7) + 1
        return month, week

    def generate_weekly_report(self, user_id, tz):
        """주간 리포트 생성"""
        from .summarize_weekly_report import SummarizeWeeklyReport
        self.summarizer = SummarizeWeeklyReport()
        
        # 현재 날짜로부터 월과 주차 계산
        now = datetime.now(tz)
        month, week = self.get_week_info(now)

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
        prompt = WEEKLY_REPORT_PROMPT.format(month=month, week=week, sections=sections)
        messages = [
            {"role": "system", "content": "아래 프롬프트에 따라 Weekly Report 마크다운을 생성해줘. 반드시 예시 구조와 순서를 지켜야 해."},
            {"role": "user", "content": prompt}
        ]

        error_response = f"# Weekly Report – {month}월 {week}주차\n(데이터 없음)"
        return self._call_llm(messages, error_response)

    def generate_weekly_report_script(self, user_id, markdown=None, tz=None):
        """주간 리포트 브리핑 스크립트 생성"""
        if tz is None:
            tz = TimeUtils.get_timezone("UTC")
        if markdown is None:
            markdown = self.generate_weekly_report(user_id, tz)
            
        now = datetime.now(tz)
        month, week = self.get_week_info(now)
        now_time = now.strftime("%H:%M")
        
        prompt = WEEKLY_REPORT_SCRIPT_PROMPT.format(
            month=month, 
            week=week, 
            now_time=now_time, 
            markdown=markdown
        )
        
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
        total_schedules = self.schedule_service.get_schedule_count_by_date_range(
            user_id, month_start, month_end
        )
        completed_schedules = self.schedule_service.get_schedule_count_by_date_range(
            user_id, month_start, month_end, status='done'
        )
        return {
            'total': total_schedules,
            'completed': completed_schedules,
            'completion_rate': completed_schedules / total_schedules if total_schedules > 0 else 0
        }