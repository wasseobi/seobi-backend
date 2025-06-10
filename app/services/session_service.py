import json
import uuid
from datetime import datetime, timezone
from typing import List, Optional, Dict, Any

from app.dao.session_dao import SessionDAO
from app.utils.json_utils import extract_json_string
from app.utils.openai_client import get_completion

class SessionService:
    def __init__(self):
        self.session_dao = SessionDAO()

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
        sessions = self.session_dao.get_all()
        return [self._serialize_session(session) for session in sessions]

    def get_user_sessions(self, user_id: uuid.UUID) -> List[Dict]:
        sessions = self.session_dao.get_all_by_user_id(user_id)
        return [self._serialize_session(session) for session in sessions]

    def get_session(self, session_id: uuid.UUID) -> Optional[Dict]:
        # TODO(GideokKim): 나중에 `get`으로 통일할지 아니면 `get_by_id`로 통일할지 결정해야 함.
        session = self.session_dao.get_by_id(session_id)
        if not session:
            # TODO(GideokKim): 찾지 못했을 때 raise할지 return None할지 결정해야 함.
            raise ValueError('Session not found')
        return self._serialize_session(session)

    def create_session(self, user_id: uuid.UUID) -> Dict:
        session = self.session_dao.create(user_id)
        if not session:
            # TODO(GideokKim): 생성 실패했을 때 raise할지 return None할지 결정해야 함.
            raise ValueError('Failed to create session')
        return self._serialize_session(session)

    def update_session(self, session_id: uuid.UUID, title: Optional[str] = None,
                       description: Optional[str] = None, finish_at: Optional[datetime] = None) -> Dict:
        update_data = {}
        if title is not None:
            update_data['title'] = title
        if description is not None:
            update_data['description'] = description
        if finish_at is not None:
            update_data['finish_at'] = finish_at

        session = self.session_dao.update(session_id, **update_data)
        if not session:
            # TODO(GideokKim): 업데이트 실패했을 때 raise할지 return None할지 결정해야 함.
            raise ValueError('Session not found')
        return self._serialize_session(session)

    def finish_session(self, session_id: uuid.UUID) -> Dict:
        """Finish a session with validation"""
        session = self.session_dao.get_by_id(session_id)
        if not session:
            raise ValueError('Session not found')
        if session.finish_at:
            raise ValueError('Session is already finished')

        current_time = datetime.now(timezone.utc)
        updated_session = self.session_dao.update_finish_time(session_id, current_time)
        if not updated_session:
            # TODO(GideokKim): 업데이트 실패했을 때 raise할지 return None할지 결정해야 함.
            raise ValueError('Failed to update session finish time')
        
        return self._serialize_session(updated_session)

    def update_session_summary(self, session_id: uuid.UUID,
                                    context_messages: List[Dict[str, str]]) -> Dict:
        self.get_session(session_id)

        # TODO(GideokKim): OpenAI API 호출과 응답을 받을 위치를 고민해볼 필요 있음.
        response = get_completion(context_messages)

        try:
            json_str = extract_json_string(response)
            result = json.loads(json_str)
            title = result.get('title')
            description = result.get('description')
            
            if not title:
                title = "당신을 이해하고 보조하는 비서, 서비입니다."
            if not description:
                description = ("서비를 사용해주셔서 감사합니다. "
                               "서비는 Microsoft AI School 6기 수강생 중 1팀이 진행한 마지막 프로젝트의 결과물입니다. "
                               "이 프로젝트는 최초 개발 당시 총 7명의 수강생이 참여했으며, 팀원은 다음과 같습니다.\n\n"
                               "권동훈, 김기덕, 김용휘, 김지강, 박주은, 박주형, 이현령")
            session = self.session_dao.update(
                session_id,
                title=title,
                description=description
            )
            return self._serialize_session(session)
        except Exception as e:
            # NOTE(GideokKim): 예외 발생 시에도 title과 description 모두 설정
            fallback_title = response[:20] if response else "대화 요약"
            fallback_description = response[:100] if response else "요약을 생성하는 중 오류가 발생했습니다."
            session = self.session_dao.update(
                session_id,
                title=fallback_title,
                description=fallback_description
            )
            return self._serialize_session(session)

    def delete_session(self, session_id: uuid.UUID) -> bool:
        return self.session_dao.delete(str(session_id))
