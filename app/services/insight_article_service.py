from app.dao.insight_article_dao import InsightArticleDAO
from app.services.interest_service import InterestService
from app.utils.openai_client import get_openai_client, get_completion
from app.utils.prompt.service_prompts import INSIGHT_ARTICLE_SYSTEM_PROMPT
from app.langgraph.insight.graph import build_insight_graph

from datetime import datetime, timezone

class InsightArticleService:
    def __init__(self):
        self.insight_article_dao = InsightArticleDAO()
        self.interest_service = InterestService()

    def create_article(self, user_id, type):
        """
        insight 그래프를 실행하고, 결과 context를 받아 DB에 저장
        """
        graph = build_insight_graph()
        context = {"user_id": user_id, "type": type}
        result = graph.invoke(context)
        data = {
            "user_id": user_id,
            "title": result.get("title", ""),
            "content": result.get("text", ""),
            "tags": result.get("tags", []),
            "source": result.get("source", []),
            "type": type,
            "created_at": datetime.now(timezone.utc),
            "keywords": result.get("keywords", []),
            "interest_ids": result.get("interest_ids", []),
            "script": result.get("script", "")
        }
        return self.insight_article_dao.create(**data)

    def get_user_articles_by_date(self, user_id):
        articles = self.insight_article_dao.get_by_user(user_id)
        return sorted(articles, key=lambda a: a.created_at, reverse=True)

    def get_article(self, article_id):
        return self.insight_article_dao.get_by_id(article_id)

    def delete_article(self, article_id):
        return self.insight_article_dao.delete(article_id)
