from app.dao.base import BaseDAO
from app.dao.base import BaseDAO
from app.models import InsightArticle, db
from typing import List, Optional
import uuid
from typing import List, Optional
import uuid

class InsightArticleDAO(BaseDAO[InsightArticle]):

    def __init__(self):
        super().__init__(InsightArticle)

    def get_all_articles(self) -> List[InsightArticle]:
        """Get all articles ordered by created_at desc"""
        return self.query().order_by(InsightArticle.created_at.desc()).all()
    def get_all_articles(self) -> List[InsightArticle]:
        """Get all articles ordered by created_at desc"""
        return self.query().order_by(InsightArticle.created_at.desc()).all()

    def get_article_by_id(self, article_id: uuid.UUID) -> Optional[InsightArticle]:
        """Get an article by ID"""
        return self.get(str(article_id))

    def get_user_articles(self, user_id: uuid.UUID) -> List[InsightArticle]:
        """Get all articles for a user ordered by created_at desc"""
        return self.query().filter_by(user_id=user_id).order_by(InsightArticle.created_at.desc()).all()

    def create(self, user_id: uuid.UUID, **kwargs) -> InsightArticle:
        """Create a new article with user_id"""
        return super().create(user_id=user_id, **kwargs)

    def update_article(self, article_id: uuid.UUID, **kwargs) -> Optional[InsightArticle]:
        """Update an article with specific fields"""
        return self.update(str(article_id), **kwargs)