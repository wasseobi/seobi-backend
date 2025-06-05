import uuid
from typing import List, Optional
from datetime import datetime

from app.models import InsightArticle
from app.dao.base import BaseDAO

class InsightArticleDAO(BaseDAO[InsightArticle]):

    def __init__(self):
        super().__init__(InsightArticle)

    def get_all_by_id(self, article_id: uuid.UUID) -> Optional[InsightArticle]:
        """Get an article by ID"""
        return self.get(str(article_id))

    def get_all_by_user_id(self, user_id: uuid.UUID) -> List[InsightArticle]:
        """Get all articles for a user ordered by created_at desc"""
        return self.query().filter_by(user_id=user_id).order_by(InsightArticle.created_at.desc()).all()

    def get_all_by_user_id_in_range(self, user_id: uuid.UUID, start: datetime, end: datetime) -> List[InsightArticle]:
        """Get all insight_article for a user in a given datetime range."""
        return InsightArticle.query.filter_by(user_id=user_id)\
            .filter(InsightArticle.created_at >= start, InsightArticle.created_at < end)\
            .order_by(InsightArticle.created_at.asc()).all()

    def create(self, user_id: uuid.UUID, **kwargs) -> InsightArticle:
        return super().create(user_id=user_id, **kwargs)

    def update(self, article_id: uuid.UUID, **kwargs) -> Optional[InsightArticle]:
        return super().update(str(article_id), **kwargs)