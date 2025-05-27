from app.models import InsightArticle, db

class InsightArticleDAO:
    def get_by_user(self, user_id):
        return InsightArticle.query.filter_by(user_id=user_id).all()

    def get(self, article_id):
        return InsightArticle.query.get(article_id)

    def create(self, **kwargs):
        article = InsightArticle(**kwargs)
        db.session.add(article)
        db.session.commit()
        return article

    def delete(self, article_id):
        article = self.get(article_id)
        if article:
            db.session.delete(article)
            db.session.commit()
            return True
        return False
