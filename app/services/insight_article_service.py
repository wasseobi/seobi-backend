from app.dao.insight_article_dao import InsightArticleDAO
from app.services.interest_service import InterestService
from app.utils.openai_client import get_openai_client, get_completion
from app.services.prompts import INSIGHT_ARTICLE_SYSTEM_PROMPT

from datetime import datetime, timezone

class InsightArticleService:
    def __init__(self):
        self.insight_article_dao = InsightArticleDAO()
        self.interest_service = InterestService()

    # def create_article(self, user_id, type):
    #     # 상위 3개 interest 추출
    #     top_interests = sorted(
    #         self.interest_service.get_interests_by_user(user_id),
    #         key=lambda i: i.importance,
    #         reverse=True
    #     )[:3]
    #     keywords = [i.content for i in top_interests]
    #     interest_ids = [str(i.id) for i in top_interests]
        
    #     client = get_openai_client()
    #     response = get_completion(client, context_messages)

    #     data = {
    #         "user_id": user_id,
    #         "title": title,
    #         "content": response,
    #         "tags": tags,
    #         "source": source,
    #         "type": type,
    #         "created_at": datetime.now(timezone.utc),
    #         "keywords": keywords,
    #         "interest_ids": interest_ids,
    #     }
    #     return self.insight_article_dao.create(**data)

    def get_user_articles_by_date(self, user_id):
        articles = self.insight_article_dao.get_by_user(user_id)
        return sorted(articles, key=lambda a: a.created_at, reverse=True)

    def get_article(self, article_id):
        return self.insight_article_dao.get_by_id(article_id)

    def delete_article(self, article_id):
        return self.insight_article_dao.delete(article_id)
