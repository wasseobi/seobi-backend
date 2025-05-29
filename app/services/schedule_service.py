from app.dao.schedule_dao import ScheduleDAO
import datetime
from app.langgraph.parsing_agent.graph import parsing_agent

class ScheduleService:
    def __init__(self):
        self.dao = ScheduleDAO()

    def get_user_schedule(self, user_id):
        return self.dao.get_by_user(user_id)

    def get_schedule(self, schedule_id):
        return self.dao.get(schedule_id)

    def create(self, data):
        return self.dao.create(**data)

    def delete(self, schedule_id):
        return self.dao.delete(schedule_id)

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
