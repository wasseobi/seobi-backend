from app.dao.base import BaseDAO
from app.models import InsightArticle, db
from typing import List, Optional
import json
import uuid

class InsightArticleDAO(BaseDAO[InsightArticle]):

    def __init__(self):
        super().__init__(InsightArticle)

    def get_all_articles(self) -> List[InsightArticle]:
        """Get all articles ordered by created_at desc"""
        return self.query().order_by(InsightArticle.created_at.desc()).all()

    def get_article_by_id(self, article_id: uuid.UUID) -> Optional[InsightArticle]:
        """Get an article by ID"""
        return self.get(str(article_id))

    def get_user_articles(self, user_id: uuid.UUID) -> List[InsightArticle]:
        """Get all articles for a user ordered by created_at desc"""
        return self.query().filter_by(user_id=user_id).order_by(InsightArticle.created_at.desc()).all()

    def create(self, **kwargs):
        article = InsightArticle(
            title=kwargs.get('title'),
            content=json.dumps(kwargs.get('content', {}), ensure_ascii=False),
            user_id=kwargs.get('user_id'),
            created_at=kwargs.get('created_at'),
            type=kwargs.get('type'),
            keywords=json.dumps(kwargs.get('keywords', []), ensure_ascii=False),
            interest_ids=kwargs.get('interest_ids'),
            tags=json.dumps(kwargs.get('tags', []), ensure_ascii=False),
            source=json.dumps(kwargs.get('source', []), ensure_ascii=False)
        )
        db.session.add(article)
        db.session.commit()
        return article


    def update_article(self, article_id: uuid.UUID, **kwargs) -> Optional[InsightArticle]:
        """Update an article with specific fields"""
        return self.update(str(article_id), **kwargs)