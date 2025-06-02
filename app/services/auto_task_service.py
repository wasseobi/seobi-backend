from app.dao.auto_task_dao import AutoTaskDAO
from typing import List, Optional, Dict, Any

class AutoTaskService:
    def __init__(self):
        self.auto_task_dao = AutoTaskDAO()

    def _serialize_auto_task(self, auto_task: Any) -> Dict[str, Any]:
        """Serialize message data for API response"""
        return {
            'id': str(auto_task.id),
            'user_id': str(auto_task.user_id),
            'title': auto_task.title,
            'repeat': auto_task.repeat,
            'created_at': auto_task.created_at.isoformat() if auto_task.created_at else None,
            'start_at': auto_task.start_at.isoformat() if auto_task.start_at else None,
            'finish_at': auto_task.finish_at.isoformat() if auto_task.finish_at else None,
            'tool': auto_task.tool,
            'status': auto_task.status,
            'linked_service': auto_task.linked_service
        }

    def get_all_auto_tasks(self) -> List[Dict]:
        auto_tasks = self.auto_task_dao.get_all_auto_tasks()
        return [self._serialize_auto_task(auto_task) for auto_task in auto_tasks]

    def get_auto_task_by_id(self, auto_task_id)-> Dict:
        auto_task = self.auto_task_dao.get_auto_task_by_id(auto_task_id)
        if not auto_task:
            raise ValueError('auto_task not found')
        return self._serialize_auto_task(auto_task)
    
    def get_user_auto_tasks(self, user_id) -> List[Dict]:
        auto_tasks = self.auto_task_dao.get_user_auto_tasks(user_id)
        if not auto_tasks:
            raise ValueError(f"No auto_tasks found for user {user_id}")
        return [self._serialize_auto_task(auto_task) for auto_task in auto_tasks]
    
    def get_all_by_user_id_in_range(self, user_id, start, end, status=None) -> List[Dict]:
        """
        주어진 기간(start~end)과 상태(status)에 해당하는 사용자의 AutoTask 목록을 반환
        """
        auto_tasks = self.auto_task_dao.get_all_by_user_id_in_range(user_id, start, end, status)
        if not auto_tasks:
            raise ValueError('No auto_tasks found in range')
        return [self._serialize_auto_task(auto_task) for auto_task in auto_tasks]

    def create(self, user_id, **data) -> Dict:
        auto_task = self.auto_task_dao.create(user_id=user_id, **data)
        return self._serialize_auto_task(auto_task)

    def update(self, auto_task_id, **kwargs) -> Dict:
        auto_task = self.auto_task_dao.update(auto_task_id, **kwargs)
        if not auto_task:
            raise ValueError('auto_task not found')
        return self._serialize_auto_task(auto_task)

    # NOTE(juaa): `update` method를 써도 되지만 타입 안전성, 명확성, 유지보수성 등을 위해 사용
    def update_finish_time(self, auto_task_id, finish_time) -> Dict:
        auto_task = self.auto_task_dao.update_finish_time(auto_task_id, finish_time)
        if not auto_task:
            raise ValueError('auto_task not found')
        return self._serialize_auto_task(auto_task)

    # NOTE(juaa): `update` method를 써도 되지만 타입 안전성, 명확성, 유지보수성 등을 위해 사용
    def update_status(self, auto_task_id, status) -> Dict:
        auto_task = self.auto_task_dao.update_status(auto_task_id, status)
        if not auto_task:
            raise ValueError('auto_task not found')
        return self._serialize_auto_task(auto_task)

    def delete(self, auto_task_id) -> bool:
        result = self.auto_task_dao.delete(auto_task_id)
        if not result:
            raise ValueError('auto_task not found')
        return result

