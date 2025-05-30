import json
from app.utils.openai_client import get_openai_client, get_completion
from app.utils.prompt.reports.daily_report_prompts import (
    SCHEDULES_MARKDOWN_PROMPT,
    SESSIONS_MARKDOWN_PROMPT,
    ARTICLES_MARKDOWN_PROMPT,
)
from .get_report_service import GetReportService

class SummarizeReportService:
    def __init__(self):
        self.getter = GetReportService()

    def summarize_schedules_done(self, user_id, tz, max_retries=2):
        schedules = self.getter.get_today_schedules_done(user_id, tz)
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

    def summarize_schedules_undone(self, user_id, tz, max_retries=2):
        schedules = self.getter.get_today_schedules_undone(user_id, tz)
        count = len(schedules)
        schedules_json = json.dumps(schedules, ensure_ascii=False)
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

    def summarize_tomorrow_schedules(self, user_id, tz, max_retries=2):
        schedules = self.getter.get_tomorrow_schedules(user_id, tz)
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

    def summarize_sessions(self, user_id, tz, max_retries=2):
        sessions = self.getter.get_today_sessions(user_id, tz)
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

    def summarize_today_articles(self, user_id, tz, max_retries=2):
        articles = self.getter.get_today_articles(user_id, tz)
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
