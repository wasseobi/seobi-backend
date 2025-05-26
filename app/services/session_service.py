import uuid
import json
from datetime import datetime, timezone, timedelta
from typing import List, Optional, Dict, Any

from app.dao.session_dao import SessionDAO
from app.utils.openai_client import get_openai_client, get_completion

# Define KST timezone (UTC+9)
KST = timezone(timedelta(hours=9))


class SessionService:
    def __init__(self):
        self.dao = SessionDAO()

    def _serialize_session(self, session: Any) -> Dict[str, Any]:
        """Serialize session data for API response"""
        return {
            'id': str(session.id),
            'user_id': str(session.user_id),
            'start_at': session.start_at.isoformat() if session.start_at else None,
            'finish_at': session.finish_at.isoformat() if session.finish_at else None,
            'title': session.title,
            'description': session.description
        }

    def get_all_sessions(self) -> List[Dict]:
        """Get all sessions"""
        sessions = self.dao.get_all_sessions()
        return [self._serialize_session(session) for session in sessions]

    def get_session(self, session_id: uuid.UUID) -> Optional[Dict]:
        """Get a session by ID"""
        session = self.dao.get_session_by_id(session_id)
        if not session:
            raise ValueError('Session not found')
        return self._serialize_session(session)

    def create_session(self, user_id: uuid.UUID) -> Dict:
        """Create a new session with validation"""
        # User validation should be moved to UserDAO
        session = self.dao.create_session(user_id)
        if not session:
            raise ValueError('Failed to create session')
        return self._serialize_session(session)

    def update_session(self, session_id: uuid.UUID, title: Optional[str] = None,
                       description: Optional[str] = None, finish_at: Optional[datetime] = None) -> Dict:
        """Update a session with validation"""
        update_data = {}
        if title is not None:
            update_data['title'] = title
        if description is not None:
            update_data['description'] = description
        if finish_at is not None:
            update_data['finish_at'] = finish_at

        session = self.dao.update_session(session_id, **update_data)
        if not session:
            raise ValueError('Session not found')
        return self._serialize_session(session)

    def delete_session(self, session_id: uuid.UUID) -> None:
        """Delete a session"""
        if not self.dao.delete_session(session_id):
            raise ValueError('Session not found')

    def finish_session(self, session_id: uuid.UUID) -> Dict:
        """Finish a session with validation"""
        session = self.dao.get_session_by_id(session_id)
        if not session:
            raise ValueError('Session not found')
        if session.finish_at:
            raise ValueError('Session is already finished')

        current_time = datetime.now(KST)
        updated_session = self.dao.update_finish_time(session_id, current_time)
        if not updated_session:
            raise ValueError('Failed to update session finish time')

        return self._serialize_session(updated_session)

    def update_summary_conversation(self, session_id: uuid.UUID,
                                    user_message: str, assistant_message: str) -> None:
        """Update session title and description based on conversation"""
        try:
            context_messages = [
                {"role": "system", "content": "다음 대화를 바탕으로 세션의 제목과 설명을 생성해주세요. "
                 "제목은 20자 이내로, 설명은 100자 이내로 작성해주세요. "
                 "응답은 JSON 형식으로 'title'과 'description' 키를 포함해야 합니다."},
                {"role": "user", "content": "다음 대화를 바탕으로 세션의 제목과 설명을 생성해주세요:\n\n"
                 f"user: {user_message}\n"
                 f"assistant: {assistant_message}"}
            ]

            client = get_openai_client()
            response = get_completion(client, context_messages)

            try:
                result = json.loads(response)
                if 'title' in result and 'description' in result:
                    self.dao.update_session(
                        session_id,
                        title=result['title'],
                        description=result['description']
                    )
            except json.JSONDecodeError:
                self.dao.update_session(
                    session_id,
                    description=response[:100]
                )
        except Exception as e:
            print(f"Failed to update session title/description: {str(e)}")
            # Don't raise the exception to prevent blocking the main flow
            # Just log the error and continue

    def get_user_sessions(self, user_id: uuid.UUID) -> List[Dict]:
        """Get all sessions for a user

        Args:
            user_id (uuid.UUID): User's ID

        Returns:
            List[Dict]: List of serialized sessions for the user

        Raises:
            ValueError: If user_id is invalid
        """
        try:
            sessions = self.dao.get_user_sessions(user_id)
            return [{
                'id': str(session.id),
                'user_id': str(session.user_id),
                'title': session.title,
                'description': session.description,
                'start_at': session.start_at.isoformat() if session.start_at else None,
                'finish_at': session.finish_at.isoformat() if session.finish_at else None
            } for session in sessions]
        except Exception as e:
            raise ValueError(f"Failed to get sessions for user {user_id}")
