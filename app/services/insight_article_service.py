from app.dao.insight_article_dao import InsightArticleDAO

class InsightArticleService:
    def __init__(self):
        self.dao = InsightArticleDAO()

    def get_user_articles(self, user_id):
        return self.dao.get_by_user(user_id)

    def get_article(self, article_id):
        return self.dao.get(article_id)

    def create_article(self, data):
        return self.dao.create(**data)

    def delete_article(self, article_id):
        return self.dao.delete(article_id)
