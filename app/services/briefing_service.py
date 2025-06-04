import uuid
from typing import List, Optional, Dict, Any

from app.dao.briefing_dao import BriefingDAO

class BriefingService:
    def __init__(self):
        self.briefing_dao = BriefingDAO()

    def _serialize_briefing(self, briefing) -> Dict[str, Any]:
        return {
            'id': str(briefing.id),
            'user_id': str(briefing.user_id),
            'content': briefing.content,
            'created_at': briefing.created_at.isoformat()
        }
    
    def get_all_briefings(self) -> List[Dict]:
        briefings = self.briefing_dao.get_all()
        return [self._serialize_briefing(b) for b in briefings]

    def get_briefing(self, briefing_id: uuid.UUID) -> Optional[Dict]:
        briefing = self.briefing_dao.get_by_id(briefing_id)
        if not briefing:
            raise ValueError('Briefing not found')
        return self._serialize_briefing(briefing)

    def get_user_briefings(self, user_id: uuid.UUID) -> List[Dict]:
        briefings = self.briefing_dao.get_all_by_user_id(user_id)
        return [self._serialize_briefing(b) for b in briefings]

    def create_briefing(self, user_id: uuid.UUID, content: str) -> Dict:
        briefing = self.briefing_dao.create(user_id=user_id, content=content)
        return self._serialize_briefing(briefing)

    def update_briefing(self, briefing_id: uuid.UUID, content: Optional[str] = None) -> Optional[Dict]:
        briefing = self.briefing_dao.update(briefing_id, content=content)
        if not briefing:
            raise ValueError('Briefing not found')
        return self._serialize_briefing(briefing)

    def delete_briefing(self, briefing_id: uuid.UUID) -> bool:
        return self.briefing_dao.delete(briefing_id) 
