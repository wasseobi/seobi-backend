import json

from app.dao.interest_dao import InterestDAO
from app.dao.session_dao import SessionDAO
from app.utils.openai_client import get_openai_client, get_completion
from app.utils.prompt.service_prompts import (
    EXTRACT_KEYWORDS_SYSTEM_PROMPT, get_interest_user_prompt)


class InterestService:
    def __init__(self):
        self.interest_dao = InterestDAO()
        self.session_dao = SessionDAO()

    def create_interest(self, user_id, content, source_message, importance=0.5):
        return self.interest_dao.create(user_id, content, source_message, importance)

    def get_interest_by_id(self, interest_id):
        return self.interest_dao.get_all(interest_id)

    def get_interests_by_user(self, user_id):
        return self.interest_dao.get_all_by_user_id(user_id)
    
    def get_all_by_user_id_date_range(self, user_id, start, end):
        return self.interest_dao.get_all_by_user_id_date_range(user_id, start, end)

    def update_interest(self, interest_id, **kwargs):
        return self.interest_dao.update(interest_id, **kwargs)

    def delete_interest(self, interest_id):
        return self.interest_dao.delete(interest_id)

    def extract_interests_keywords(self, session_id):
        # 1. 세션의 모든 메시지 조회
        from app.services.message_service import MessageService
        self.message_service = MessageService()
        messages = self.message_service.get_session_messages(session_id)

        # 1-1. session_id로 session 조회
        session = self.session_dao.get_by_id(session_id)

        # 메시지 포맷: [{'id': '...', 'content': '...'}, ...]
        message_list = [
            {"id": str(msg["id"]), "content": msg["content"]} for msg in messages
        ]

        # 기존 키워드 리스트 추출
        interests = self.interest_dao.get_all_by_user_id(session.user_id)
        user_keywords = [interest.content for interest in interests]

        # 2. 프롬프트 생성 (기존 키워드 리스트 포함)
        user_prompt = get_interest_user_prompt(message_list, user_keywords)

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
            # 기존 키워드 importance 감소 및 update
            for interest in interests:
                interest.importance *= 0.9  # 예시: 10% 감소
                self.interest_dao.update(interest.id, importance=interest.importance)
            # 새 키워드 처리
            for item in result:
                keyword = item["keyword"]
                importance = item.get("importance", 0.5)
                self.interest_dao.create(
                    user_id=session.user_id,
                    content=keyword,
                    source_message=item["message_ids"],
                    importance=importance
                )
        except Exception as e:
            print(f"[InterestService] LLM 결과 파싱 실패: {e}\n응답: {response}")
