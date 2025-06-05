from datetime import timezone
from typing import Any, Dict, List, Optional
from uuid import UUID

from app.dao.schedule_dao import ScheduleDAO
from app.langgraph.parsing_agent.graph import parsing_agent
from app.utils.time import TimeUtils


class ScheduleService:
    def __init__(self):
        self.schedule_dao = ScheduleDAO()

    def get_user_schedules(self, user_id):
        return self.schedule_dao.get_all_by_user_id(user_id)

    def get_schedule(self, schedule_id):
        return self.schedule_dao.get_by_id(schedule_id)

    def get_by_date_range_status(self, user_id: UUID, start, end,
                                 status: Optional[str] = None) -> List[Dict]:
        """주간 일정 조회"""
        return self.schedule_dao.get_all_by_user_id_in_range_status(
            user_id, start, end, status=status
        )

    def get_count_by_date_range(self, user_id: UUID, start, end,
                                status: Optional[str] = None) -> int:
        return self.schedule_dao.get_count_by_date_range(
            user_id, start, end, status=status
        )
    
    def get_all_by_ongoing(self, user_id: UUID, current_time: timezone) -> List[Dict]:
        """현재 진행 중인 일정 조회 (시작했지만 아직 완료되지 않은 일정)"""
        return self.schedule_dao.get_all_by_ongoing(user_id, current_time)

    def create(self, data):
        return self.schedule_dao.create(**data)

    def delete(self, schedule_id):
        return self.schedule_dao.delete(schedule_id)

    def create_llm(self, user_id, text):
        """
        자연어 파싱 에이전트 그래프(parsing_agent)를 활용해 일정 생성.
        """
        input_data = {
            'user_id': user_id,
            'text': text
        }
        result = parsing_agent(input_data)
        # 그래프 결과에서 일정 생성에 필요한 데이터 추출 (stub)
        parsed_data = {
            'user_id': user_id,
            'title': result.get('title', '팀 미팅'),
            'repeat': result.get('repeat', ''),
            'start_at': result.get('start_at', None),
            'finish_at': result.get('finish_at', None),
            'location': result.get('location', ''),
            'status': result.get('status', 'undone'),
            'memo': result.get('memo', ''),
            'linked_service': result.get('linked_service', ''),
        }
        return self.create(parsed_data)
