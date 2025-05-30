import uuid
import json
import re
from datetime import datetime, timezone
from typing import List, Optional, Dict, Any

from app.dao.session_dao import SessionDAO
from app.utils.openai_client import get_openai_client, get_completion
from app.utils.prompt.service_prompts import (
    SESSION_SUMMARY_SYSTEM_PROMPT,
    SESSION_SUMMARY_USER_PROMPT
)

class SessionService:
    def __init__(self):
        self.session_dao = SessionDAO()
        self._cleanup_executor = None

    @property
    def cleanup_executor(self):
        """Lazy initialization of cleanup executor."""
        if self._cleanup_executor is None:
            from app.langgraph.cleanup.executor import create_cleanup_executor
            self._cleanup_executor = create_cleanup_executor()
        return self._cleanup_executor

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
        sessions = self.session_dao.get_all()
        return [self._serialize_session(session) for session in sessions]

    def get_session(self, session_id: uuid.UUID) -> Optional[Dict]:
        """Get a session by ID"""
        session = self.session_dao.get_by_id(session_id)
        if not session:
            raise ValueError('Session not found')
        return self._serialize_session(session)

    def create_session(self, user_id: uuid.UUID) -> Dict:
        """Create a new session with validation"""
        # User validation should be moved to UserDAO
        session = self.session_dao.create(user_id)
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

        session = self.session_dao.update_session(session_id, **update_data)
        if not session:
            raise ValueError('Session not found')
        return self._serialize_session(session)

    def delete_session(self, session_id: uuid.UUID) -> None:
        """Delete a session"""
        if not self.session_dao.delete(session_id):
            raise ValueError('Session not found')

    def finish_session(self, session_id: uuid.UUID) -> Dict:
        """Finish a session with validation and run cleanup graph"""
        session = self.session_dao.get_by_id(session_id)
        if not session:
            raise ValueError('Session not found')
        if session.finish_at:
            raise ValueError('Session is already finished')

        # Get conversation history
        conversation_history = self.session_dao.get_session_messages(session_id)

        current_time = datetime.now(timezone.utc)
        updated_session = self.session_dao.update_finish_time(session_id, current_time)
        if not updated_session:
            raise ValueError('Failed to update session finish time')

        try:
            # Run cleanup using executor
            cleanup_result = self.cleanup_executor(session_id, conversation_history)
            
            # TODO(noah): 추후 삭제하고 실제 Auto task table에 저장하는 기능으로 대체해야 함.
            if cleanup_result.get("error"):
                print(f"Cleanup failed for session {session_id}: {cleanup_result['error']}")
            else:
                print(f"Cleanup completed for session {session_id}")
                print(f"Analysis: {cleanup_result.get('analysis_result')}")
                print(f"Generated tasks: {cleanup_result.get('generated_tasks')}")
        except Exception as e:
            print(f"Error during cleanup: {str(e)}")
            # Cleanup 실패는 세션 종료를 막지 않음
        
        return self._serialize_session(updated_session)

    def update_summary_conversation(self, session_id: uuid.UUID,
                                    user_message: str, assistant_message: str) -> None:
        """Update session title and description based on conversation"""
        def extract_json_string(s):
            s = s.strip()
            if s.startswith("```json"):
                s = s[len("```json"):].strip()
            if s.startswith("```"):
                s = s[len("```"):].strip()
            if s.startswith("json"):
                s = s[4:].strip()
            match = re.search(r'({.*})', s, re.DOTALL)
            if match:
                return match.group(1)
            return s

        try:
            context_messages = [
                {"role": "system", "content": SESSION_SUMMARY_SYSTEM_PROMPT},
                {"role": "user", "content": SESSION_SUMMARY_USER_PROMPT +
                 f"user: {user_message}\n"
                 f"assistant: {assistant_message}"}
            ]

            client = get_openai_client()
            response = get_completion(client, context_messages)

            try:
                json_str = extract_json_string(response)
                result = json.loads(json_str)
                title = result.get('title')
                description = result.get('description')
                # fallback: title/description이 None이거나 빈 문자열이면 일부라도 채워넣기
                if not title:
                    title = (description or response)[:20]
                if not description:
                    description = response[:100]
                self.session_dao.update_session(
                    session_id,
                    title=title,
                    description=description
                )
            except json.JSONDecodeError:
                self.session_dao.update_session(
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
            sessions = self.session_dao.get_user_sessions(user_id)
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

    def summarize_session(self, session_id: uuid.UUID) -> None:
        """
        세션의 모든 메시지를 기반으로 title/description 요약을 생성하고 세션에 저장
        """
        from app.services.message_service import MessageService
        message_service = MessageService()
        messages = message_service.get_session_messages(session_id)
        dialogue = "\n".join(
            f"{m['role']}: {m['content']}" for m in messages if m['role'] in ('user', 'assistant') and m.get('content')
        )
        def extract_json_string(s):
            s = s.strip()
            if s.startswith("```json"):
                s = s[len("```json"):].strip()
            if s.startswith("```"):
                s = s[len("```"):].strip()
            if s.startswith("json"):
                s = s[4:].strip()
            match = re.search(r'({.*})', s, re.DOTALL)
            if match:
                return match.group(1)
            return s
        context_messages = [
            {"role": "system", "content": SESSION_SUMMARY_SYSTEM_PROMPT},
            {"role": "user", "content": dialogue}
        ]
        client = get_openai_client()
        response = get_completion(client, context_messages)
        try:
            json_str = extract_json_string(response)
            result = json.loads(json_str)
            title = result.get('title')
            description = result.get('description')
            if not title:
                title = (description or response)[:20]
            if not description:
                description = response[:100]
            self.session_dao.update_session(
                session_id,
                title=title,
                description=description
            )
        except Exception as e:
            self.session_dao.update_session(
                session_id,
                description=response[:100]
            )
