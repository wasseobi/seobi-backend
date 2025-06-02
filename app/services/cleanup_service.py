from typing import Dict, Any, List
import uuid
from app.langgraph.cleanup.executor import create_cleanup_executor
from app.services.message_service import MessageService

class CleanupService:
    def __init__(self):
        self._cleanup_executor = None
        self.message_service = MessageService()

    @property
    def cleanup_executor(self):
        """Lazy initialization of cleanup executor."""
        if self._cleanup_executor is None:
            self._cleanup_executor = create_cleanup_executor()
        return self._cleanup_executor

    def cleanup_session(self, session_id: uuid.UUID) -> Dict[str, Any]:
        try:
            # Get conversation history
            conversation_history = self.message_service.get_session_messages(session_id)

            # Run cleanup using executor
            cleanup_result = self.cleanup_executor(session_id, conversation_history)
            
            # TODO(noah): 추후 삭제하고 실제 Auto task table에 저장하는 기능으로 대체해야 함.
            if cleanup_result.get("error"):
                print(f"Cleanup failed for session {session_id}: {cleanup_result['error']}")
            else:
                print(f"Cleanup completed for session {session_id}")
                print(f"Analysis: {cleanup_result.get('analysis_result')}")
                print(f"Generated tasks: {cleanup_result.get('generated_tasks')}")
            
            return cleanup_result
        except Exception as e:
            print(f"Error during cleanup: {str(e)}")
            return {"error": str(e)} 