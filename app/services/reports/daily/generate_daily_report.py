from datetime import datetime, timedelta, timezone
from app.utils.openai_client import get_openai_client, get_completion
from app.utils.time import TimeUtils
from app.utils.prompt.reports.daily_report_prompts import (
    DAILY_REPORT_PROMPT,
    DAILY_REPORT_SCRIPT_PROMPT
)
from .summarize_daily_report import SummarizeDailyReport

class GenerateDailyReport():
    def __init__(self):
        self.summarizer = SummarizeDailyReport()

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

    def generate_daily_report(self, user_id, tz):
        today = datetime.now(tz).strftime("%Y-%m-%d")

        done = self.summarizer.summarize_daily_schedules(
            user_id, tz, when='today', status='done')
        undone = self.summarizer.summarize_daily_schedules(
            user_id, tz, when='today', status='undone')
        tomorrow = self.summarizer.summarize_daily_schedules(
            user_id, tz, when='tomorrow', status=None)

        sessions = self.summarizer.summarize_daily_sessions(user_id, tz)
        articles = self.summarizer.summarize_daily_articles(user_id, tz)

        sections = f"{done}\n\n{undone}\n\n{tomorrow}\n\n{sessions}\n\n{articles}"

        prompt = DAILY_REPORT_PROMPT.format(today=today, sections=sections)
        messages = [
            {"role": "system", "content": "아래 프롬프트에 따라 Daily Report 마크다운을 생성해줘. 반드시 예시 구조와 순서를 지켜야 해."},
            {"role": "user", "content": prompt}
        ]

        error_response = f"# Daily Report – {today}\n(데이터 없음)"
        return self._call_llm(messages, error_response)

    def generate_daily_report_script(self, user_id, markdown=None, tz=None):
        if tz is None:
            tz = TimeUtils.get_timezone("UTC")
        if markdown is None:
            markdown = self.generate_daily_report(user_id, tz)
            
        now = datetime.now(tz)
        today = now.strftime("%m-%d")
        now_time = now.strftime("%H:%M")
        
        prompt = DAILY_REPORT_SCRIPT_PROMPT.format(
            today=today, now_time=now_time, markdown=markdown)
        
        messages = [
            {"role": "system", "content": "아래 프롬프트에 따라 Daily Report 브리핑 스크립트를 생성해줘. 반드시 예시 구조와 어조를 지켜야 해."},
            {"role": "user", "content": prompt}
        ]

        error_response = f"Daily Report 브리핑 스크립트 생성이 실패했습니다. 다음 안내가 필요하시면 말씀해주세요."
        return self._call_llm(messages, error_response)