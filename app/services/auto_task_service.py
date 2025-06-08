from app.dao.auto_task_dao import AutoTaskDAO
from typing import List, Optional, Dict, Any
import json

class AutoTaskService:
    def __init__(self):
        self.auto_task_dao = AutoTaskDAO()

    def _serialize_auto_task(self, auto_task: Any) -> Dict[str, Any]:
        """Serialize message data for API response"""
        return {
            'id': str(auto_task.id),
            'user_id': str(auto_task.user_id),
            'title': auto_task.title,
            'description': auto_task.description,
            'task_list': auto_task.task_list,
            'repeat': auto_task.repeat,
            'created_at': auto_task.created_at.isoformat() if auto_task.created_at else None,
            'start_at': auto_task.start_at.isoformat() if auto_task.start_at else None,
            'finish_at': auto_task.finish_at.isoformat() if auto_task.finish_at else None,
            'preferred_at': auto_task.preferred_at.isoformat() if auto_task.preferred_at else None,
            'active': auto_task.active,
            'tool': auto_task.tool,
            'linked_service': auto_task.linked_service,
            'current_step': auto_task.current_step,
            'status': auto_task.status,
            'output': auto_task.output,
            'meta': auto_task.meta
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

    def create_from_cleanup_result(self, user_id: str, cleanup_result: Dict[str, Any]) -> List[Dict]:
        """Create auto tasks from cleanup result"""
        created_tasks = []
        tasks = cleanup_result.get('generated_tasks', [])
        
        for task in tasks:
            auto_task_data = {
                'user_id': user_id,
                'title': task['title'],
                'description': task['description'],
                'task_list': task['dependencies'],  # dependencies를 task_list로 저장
                'status': 'undone',
            }
            created_task = self.create(**auto_task_data)
            created_tasks.append(created_task)
            
        return created_tasks

    # NOTE: (juaa): Update 사용해도 되지만 확장/유지보수/의미 명확성을 위해 만들어놨어요. 
    def background_save_result(self, task_id, result, finish_at):
        if isinstance(result, str):
            result = json.loads(result)
        self.auto_task_dao.update(
            task_id,
            output=result['summary'],
            finish_at=finish_at,
            status="done"
        )
        print("[DEBUG] 최종 DB 저장값:", result['summary'])