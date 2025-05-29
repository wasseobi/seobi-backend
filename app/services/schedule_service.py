from app.dao.schedule_dao import ScheduleDAO
import datetime

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
        LLM을 활용해 자연어 text를 파싱하여 일정 생성.
        (현재는 예시 stub)
        """
        # TODO: 실제 LLM 연동 및 파싱 로직 구현
        # 예시: 반복 주기 파싱
        repeat = ''
        if '매주' in text:
            repeat = '매주'
        elif '매월' in text:
            repeat = '매월'
        elif '격주' in text:
            repeat = '격주'
        elif any(day in text for day in ['월요일', '화요일', '수요일', '목요일', '금요일', '토요일', '일요일']):
            repeat = '특정요일'
        # 예시: 날짜/시간 파싱 (stub)
        now = datetime.datetime.now()
        start_at = None
        finish_at = None
        if '내일' in text:
            start_at = now + datetime.timedelta(days=1)
            start_at = start_at.replace(hour=10, minute=0, second=0, microsecond=0)
        elif '오늘' in text:
            start_at = now.replace(hour=10, minute=0, second=0, microsecond=0)
        # 실제로는 LLM 파싱 결과를 사용해야 함
        parsed_data = {
            'user_id': user_id,
            'title': '팀 미팅',
            'repeat': repeat,
            'start_at': start_at,
            'finish_at': finish_at,
            'location': '',
            'status': 'undone',
            'memo': text,
            'linked_service': '',
        }
        return self.create(parsed_data)
