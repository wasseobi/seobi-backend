from app.models.interest import Interest
from app.models.db import db
from sqlalchemy.exc import SQLAlchemyError
from datetime import datetime, timezone

class InterestDAO:
    def create(self, user_id, content, source_message, importance=0.5):
        interest = Interest(
            user_id=user_id,
            content=content,
            source_message=source_message,
            importance=importance,
            created_at=datetime.now(timezone.utc)
        )
        # 200개 초과 시 오래된 것 삭제
        user_interests = Interest.query.filter_by(user_id=user_id).order_by(Interest.created_at.asc()).all()
        if len(user_interests) >= 200:
            for old_interest in user_interests[:len(user_interests)-199]:
                db.session.delete(old_interest)
        db.session.add(interest)
        db.session.commit()
        return interest

    def get_interest_by_id(self, interest_id):
        return Interest.query.get(interest_id)

    def get_interests_by_user(self, user_id):
        return Interest.query.filter_by(user_id=user_id).all()

    def update(self, interest_id, **kwargs):
        interest = Interest.query.get(interest_id)
        if not interest:
            return None
        for key, value in kwargs.items():
            if hasattr(interest, key):
                setattr(interest, key, value)
        db.session.commit()
        return interest

    def delete(self, interest_id):
        interest = Interest.query.get(interest_id)
        if not interest:
            return False
        db.session.delete(interest)
        db.session.commit()
        return True
