import uuid
from datetime import datetime, timedelta, timezone
from app.services.reports.summarize_report_service import SummarizeReportService
from app.utils.openai_client import get_openai_client, get_completion
from app.utils.prompt.reports.daily_report_prompts import (
    DAILY_REPORT_PROMPT,
    REPORT_BRIEFING_PROMPT,
)
from zoneinfo import ZoneInfo

def get_timezone(tz_str):
    try:
        return ZoneInfo(tz_str)
    except Exception as e:
        print(f"[WARNING] get_timezone fallback to UTC: {e}")
        return timezone.utc

class GenerateReportService:
    def __init__(self):
        self.summarizer = SummarizeReportService()

    def generate_daily_report(self, user_id, user_name, tz, max_retries=2):
        from datetime import datetime
        today = datetime.now(tz).strftime("%Y-%m-%d")
        done = self.summarizer.summarize_schedules_done(user_id, tz, max_retries)
        undone = self.summarizer.summarize_schedules_undone(user_id, tz, max_retries)
        tomorrow = self.summarizer.summarize_tomorrow_schedules(user_id, tz, max_retries)
        sessions = self.summarizer.summarize_sessions(user_id, tz, max_retries)
        articles = self.summarizer.summarize_today_articles(user_id, tz, max_retries)
        sections = f"{done}\n\n{undone}\n\n{tomorrow}\n\n{sessions}\n\n{articles}"
        prompt = DAILY_REPORT_PROMPT.format(today=today, sections=sections)
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

    def generate_briefing_script(self, user_id, user_name, markdown=None, tz=None, max_retries=2):
        from datetime import datetime
        if tz is None:
            tz = get_timezone("UTC")
        if markdown is None:
            markdown = self.generate_daily_report(user_id, user_name, tz, max_retries)
        now = datetime.now(tz)
        today = now.strftime("%m-%d")
        now_time = now.strftime("%H:%M")
        prompt = REPORT_BRIEFING_PROMPT.format(user_name=user_name, today=today, now_time=now_time, markdown=markdown)
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

    def generate_report(self, user_id, user_name, tz=None, report_type='daily', max_retries=2):
        if tz is None:
            tz = get_timezone("UTC")
        if report_type == 'daily':
            markdown = self.generate_daily_report(user_id, user_name, tz, max_retries)
            script = self.generate_briefing_script(user_id, user_name, markdown, tz, max_retries)
        # elif report_type == 'weekly':
        #     markdown = self.generate_weekly_report(...)
        #     script = self.generate_weekly_briefing_script(...)
        # elif report_type == 'monthly':
        #     ...
        else:
            raise ValueError(f"지원하지 않는 report_type: {report_type}")
        return {
            "text": markdown,
            "script": script
        }