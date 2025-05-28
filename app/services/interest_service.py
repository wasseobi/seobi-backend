import json

from app.dao.interest_dao import InterestDAO
from app.dao.session_dao import SessionDAO
from app.services.message_service import MessageService
from app.utils.openai_client import get_openai_client, get_completion
from app.services.prompts import (
    EXTRACT_KEYWORDS_SYSTEM_PROMPT, get_interest_user_prompt)


class InterestService:
    def __init__(self):
        self.dao = InterestDAO()
        self.session_dao = SessionDAO()
        self.message_service = MessageService()

    def create_interest(self, user_id, content, source_message):
        return self.dao.create_interest(user_id, content, source_message)

    def get_interest_by_id(self, interest_id):
        return self.dao.get_interest_by_id(interest_id)

    def get_interests_by_user(self, user_id):
        return self.dao.get_interests_by_user(user_id)

    def update_interest(self, interest_id, **kwargs):
        return self.dao.update_interest(interest_id, **kwargs)

    def delete_interest(self, interest_id):
        return self.dao.delete_interest(interest_id)

    def extract_interests_keywords(self, session_id):
        # 1. 세션의 모든 메시지 조회
        messages = self.message_service.get_session_messages(session_id)

        # 1-1. session_id로 user_id 조회
        user_id = self.session_dao.get_user_id_by_session_id(session_id)

        # 메시지 포맷: [{'id': '...', 'content': '...'}, ...]
        message_list = [
            {"id": str(msg["id"]), "content": msg["content"]} for msg in messages
        ]

        # 2. 프롬프트 생성
        user_prompt = get_interest_user_prompt(message_list)

        context_messages = [
            {"role": "system", "content": EXTRACT_KEYWORDS_SYSTEM_PROMPT},
            {"role": "user", "content": user_prompt}
        ]

        # 3. LLM 호출
        client = get_openai_client()
        response = get_completion(client, context_messages)

        # 4. 결과 파싱 및 저장 (response는 LLM이 반환하는 JSON 문자열이어야 함)
        try:
            result = json.loads(response)
            for item in result:
                self.dao.create_interest(
                    user_id=user_id,
                    content=item["keyword"],
                    source_message=item["message_ids"]
                )
        except Exception as e:
            print(f"[InterestService] LLM 결과 파싱 실패: {e}\n응답: {response}")
