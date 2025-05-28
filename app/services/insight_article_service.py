from app.dao.insight_article_dao import InsightArticleDAO
from app.services.interest_service import InterestService

class InsightArticleService:
    def __init__(self):
        self.dao = InsightArticleDAO()
        self.interest_service = InterestService()

    def get_user_articles(self, user_id):
        return self.dao.get_by_user(user_id)

    def get_article(self, article_id):
        return self.dao.get(article_id)

    def create_article(self, data):
        # 인사이트 기사 생성 시 해당 user의 interest importance 일괄 감소
        user_id = data.get('user_id')
        if user_id:
            interests = self.interest_service.get_interests_by_user(user_id)
            for interest in interests:
                interest.importance *= 0.9  # 예시: 10% 감소
                self.interest_service.update_interest(interest.id, importance=interest.importance)
        return self.dao.create(**data)

    def delete_article(self, article_id):
        return self.dao.delete(article_id)
