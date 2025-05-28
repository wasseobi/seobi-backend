from app.models import InsightArticle, db

class InsightArticleDAO:
    def get_by_user(self, user_id):
        return InsightArticle.query.filter_by(user_id=user_id).all()

    def get_by_id(self, article_id):
        return InsightArticle.query.get(article_id)

    def create(self, **kwargs):
        article = InsightArticle(
            title=kwargs.get('title'),
            content=kwargs.get('content'),
            user_id=kwargs.get('user_id'),
            created_at=kwargs.get('created_at'),
            type=kwargs.get('type'),
            keywords=kwargs.get('keywords'),
            interest_ids=kwargs.get('interest_ids')
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
