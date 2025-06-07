from app.langgraph.background.executor import create_background_executor
from app.services.auto_task_service import AutoTaskService
from typing import Dict, Any
from datetime import datetime, date
import uuid

class BackgroundService:
    def __init__(self):
        self._background_executor = None
        self.auto_task_service = AutoTaskService()

    def _serialize_background(self, obj):
        # 기존 로직 그대로, self는 안 쓰더라도 필수!
        if isinstance(obj, uuid.UUID):
            return str(obj)
        if isinstance(obj, (datetime, date)):
            return obj.isoformat()
        if isinstance(obj, dict):
            return {k: self._serialize_background(v) for k, v in obj.items()}
        if isinstance(obj, list):
            return [self._serialize_background(v) for v in obj]
        return obj

    @property
    def background_executor(self):
        if self._background_executor is None:
            self._background_executor = create_background_executor()
        return self._background_executor

    def background_auto_task(self, user_id: str) -> Dict[str, Any]:
        try:
            result = self.background_executor(user_id = user_id)
            return self._serialize_background(result)
        
        except Exception as e:
            print(f"Error during background: {str(e)}")
            return {"error": str(e)}