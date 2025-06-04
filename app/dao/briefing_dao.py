import uuid
from typing import List, Optional

from app.dao.base import BaseDAO
from app.models.briefing import Briefing

class BriefingDAO(BaseDAO[Briefing]):
    """Data Access Object for Briefing model"""
    def __init__(self):
        super().__init__(Briefing)

    def get_by_id(self, briefing_id: uuid.UUID) -> Optional[Briefing]:
        return self.get(str(briefing_id))

    def get_all_by_user_id(self, user_id: uuid.UUID) -> List[Briefing]:
        return self.query().filter_by(user_id=user_id).order_by(Briefing.created_at.desc()).all()

    def create(self, user_id: uuid.UUID, content: str) -> Briefing:
        return super().create(user_id=user_id, content=content)

    def update(self, briefing_id: uuid.UUID, **kwargs) -> Optional[Briefing]:
        return super().update(str(briefing_id), **kwargs)

    def delete(self, briefing_id: uuid.UUID) -> bool:
        return super().delete(str(briefing_id))
