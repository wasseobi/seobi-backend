import uuid
from typing import List, Optional, Dict, Any
from datetime import datetime, timezone, timedelta

from app.dao.briefing_dao import BriefingDAO
from app.services.reports.daily.generate_daily_report import GenerateDailyReport
from app.utils.time_utils import TimeUtils

class BriefingService:
    def __init__(self):
        self.briefing_dao = BriefingDAO()
        self.daily_report_generator = GenerateDailyReport()
        self.time_utils = TimeUtils()
        self.kst = timezone(timedelta(hours=9))

    def _serialize_briefing(self, briefing) -> Dict[str, Any]:
        return {
            'id': str(briefing.id),
            'user_id': str(briefing.user_id),
            'content': briefing.content,
            'script': briefing.script,
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

    def get_user_today_briefing(self, user_id: uuid.UUID) -> Optional[Dict]:
        """특정 사용자의 오늘 브리핑 조회 (여러 개 존재할 경우 가장 최근 브리핑 반환)"""
        briefings = self.briefing_dao.get_all_by_user_id(user_id)
        today = datetime.now(timezone.utc).date()
        
        today_briefings = [
            b for b in briefings 
            if b.created_at.date() == today
        ]
        
        if not today_briefings:
            return None
            
        most_recent = max(today_briefings, key=lambda x: x.created_at)
        return self._serialize_briefing(most_recent)

    def create_briefing(self, user_id: uuid.UUID, **kwargs) -> Dict:
        briefing = self.briefing_dao.create(user_id=user_id, **kwargs)
        return self._serialize_briefing(briefing)

    def update_briefing(self, briefing_id: uuid.UUID, **kwargs) -> Optional[Dict]:
        # First get the existing briefing
        existing_briefing = self.briefing_dao.get_by_id(briefing_id)
        if not existing_briefing:
            raise ValueError('Briefing not found')
            
        # Update the script with current time if it exists
        if existing_briefing.script:
            kwargs['script'] = self.time_utils.update_script_time(existing_briefing.script)
            
        briefing = self.briefing_dao.update(briefing_id, **kwargs)
        if not briefing:
            raise ValueError('Briefing not found')
        return self._serialize_briefing(briefing)

    def delete_briefing(self, briefing_id: uuid.UUID) -> bool:
        return self.briefing_dao.delete(briefing_id) 
