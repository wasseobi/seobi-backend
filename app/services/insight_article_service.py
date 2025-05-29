from app.dao.insight_article_dao import InsightArticleDAO
from app.services.interest_service import InterestService
from app.utils.openai_client import get_openai_client, get_completion
from app.utils.prompt.service_prompts import INSIGHT_ARTICLE_SYSTEM_PROMPT
from app.langgraph.insight.graph import build_insight_graph

from datetime import datetime, timezone
import json

class InsightArticleService:
    def __init__(self):
        self.insight_article_dao = InsightArticleDAO()
        self.interest_service = InterestService()

    def create_article(self, user_id, type):
        """
        insight 그래프를 실행하고, 결과 context를 받아 DB에 저장
        content는 {text, script} 형태의 json으로 저장
        """
        graph = build_insight_graph()
        context = {"user_id": user_id, "type": type}
        result = graph.compile().invoke(context)
        content_json = {
            "text": result.get("text", ""),
            "script": result.get("script", "")
        }
        data = {
            "user_id": user_id,
            "title": result.get("title", ""),
            "content": content_json,
            "tags": result.get("tags", []),
            "source": result.get("source", []),
            "type": type,
            "created_at": datetime.now(timezone.utc),
            "keywords": result.get("keywords", []),
            "interest_ids": result.get("interest_ids", [])
        }
        return self.insight_article_dao.create(**data)

    def get_user_articles_by_date(self, user_id):
        articles = self.insight_article_dao.get_by_user(user_id)
        return sorted(articles, key=lambda a: a.created_at, reverse=True)

    def get_article(self, article_id):
        article = self.insight_article_dao.get_by_id(article_id)
        def safe_load(val):
            if isinstance(val, str):
                try:
                    return json.loads(val)
                except Exception:
                    return val
            return val
        if article:
            article.content = safe_load(article.content)
            article.tags = safe_load(article.tags)
            article.keywords = safe_load(article.keywords)
            article.source = safe_load(article.source)
        return article

    def delete_article(self, article_id):
        return self.insight_article_dao.delete(article_id)
