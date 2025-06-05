from datetime import datetime, timezone
from typing import List
import uuid

from app.dao.base import BaseDAO
from app.models.interest import Interest


class InterestDAO(BaseDAO[Interest]):
    """Data Access Object for Interest model"""

    def __init__(self):
        super().__init__(Interest)

    def get_all_by_user_id(self, user_id):
        return Interest.query.filter_by(user_id=user_id).all()
    
    def get_all_by_user_id_date_range(self, user_id: uuid.UUID, start: datetime, end: datetime) -> List[Interest]:
        """Get all interests for a user in a given datetime range."""
        return Interest.query.filter_by(user_id=user_id)\
            .filter(Interest.created_at >= start, Interest.created_at < end)\
            .order_by(Interest.created_at.asc()).all()
    
    def get_all_by_id(self, interest_id: uuid.UUID):
        """Get interest by ID"""
        return self.get(str(interest_id))

    def create(self, user_id, content, source_message, importance=0.5, created_at=None):
        try:
            # 트랜잭션 시작
            with super().query().session.begin_nested():
                # 사용자의 관심사 개수 확인
                interest_count = self.model.query.filter_by(user_id=user_id).count()
                
                # 200개 초과 시 가장 오래된 것부터 삭제
                if interest_count >= 200:
                    # 삭제할 개수 계산
                    delete_count = interest_count - 199
                    
                    # 가장 오래된 관심사들의 ID를 조회하고 삭제
                    old_interests = self.model.query.filter_by(user_id=user_id)\
                        .order_by(self.model.created_at.asc())\
                        .limit(delete_count)\
                        .all()
                    
                    if old_interests:
                        old_ids = [interest.id for interest in old_interests]
                        self.model.query.filter(self.model.id.in_(old_ids)).delete()
                
                # 새로운 관심사 생성
                if created_at is None:
                    created_at = datetime.now(timezone.utc)
                
                new_interest = super().create(
                    user_id=user_id,
                    content=content,
                    source_message=source_message,
                    importance=importance,
                    created_at=created_at
                )

                return new_interest
        except Exception as e:
            super().query().session.rollback()
            raise e

    def update(self, interest_id, **kwargs):
        return super().update(str(interest_id), **kwargs)
