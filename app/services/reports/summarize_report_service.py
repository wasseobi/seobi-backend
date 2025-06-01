import json
from app.utils.openai_client import get_openai_client, get_completion
from app.utils.prompt.reports.daily_report_prompts import (
    SCHEDULES_PROMPT,
    SESSIONS_PROMPT,
    ARTICLES_PROMPT,
)
from .get_report_service import GetReportService
from app.utils.time import TimeUtils

class SummarizeReportService:
    def __init__(self):
        self.getter = GetReportService()

    def summarize_schedules(self, user_id, tz, when='today', status=None, max_retries=2):
        schedules = self.getter.get_schedules(user_id, tz, when=when, status=status)
        count = len(schedules)
        if when == 'tomorrow':
            header = "내일 일정"
        elif status == 'done':
            header = "완료한 일정"
        elif status == 'undone':
            header = "미완료 일정"
        else:
            raise ValueError("지원하지 않는 일정 유형입니다.")
        
        prompt = SCHEDULES_PROMPT.format(header=header, count=count)
        schedules_json = json.dumps(schedules, ensure_ascii=False)
        client = get_openai_client()
        messages = [
            {"role": "system", "content": "아래 프롬프트에 따라 마크다운 요약을 생성해줘."},
            {"role": "user", "content": prompt + "\n[SCHEDULES] " + schedules_json}
        ]
        response = None
        for attempt in range(max_retries + 1):
            try:
                response = get_completion(client, messages)
                if response is not None and response.strip() != f"## {header} (총 {count}건)":
                    break
            except Exception as e:
                print(f"[WARNING] LLM 호출 실패 (attempt {attempt+1}):", e)
        if response is None or response.strip() == f"## {header} (총 {count}건)":
            print(f"[WARNING] LLM 응답이 None이거나 헤더만 반환됨. (count={count})")
            return f"## {header} (총 {count}건)"
        return response

    def summarize_sessions(self, user_id, tz, max_retries=2):
        sessions = self.getter.get_today_sessions(user_id, tz)
        count = len(sessions)
        sessions_json = json.dumps(sessions, ensure_ascii=False)
        prompt = SESSIONS_PROMPT.format(count=count)
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

    def summarize_today_articles(self, user_id, tz, max_retries=2):
        articles = self.getter.get_today_articles(user_id, tz)
        count = len(articles)
        articles_json = json.dumps(articles, ensure_ascii=False)
        prompt = ARTICLES_PROMPT.format(count=count)
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
