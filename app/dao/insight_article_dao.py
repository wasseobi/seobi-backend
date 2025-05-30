import json

from app.models import InsightArticle, db
from app.dao.base import BaseDAO

class InsightArticleDAO(BaseDAO[InsightArticle]):

    def __init__(self):
        super().__init__(InsightArticle)

    def get_by_user(self, user_id):
        return InsightArticle.query.filter_by(user_id=user_id).all()

    def get_by_id(self, article_id):
        return InsightArticle.query.get(article_id)

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

    def delete(self, article_id):
        article = self.get_by_id(article_id)
        if article:
            db.session.delete(article)
            db.session.commit()
            return True
        return False
