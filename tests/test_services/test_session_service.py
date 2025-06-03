import uuid
import pytest
from datetime import datetime, timezone
from app.services.session_service import SessionService
from app.dao.user_dao import UserDAO
from app.models.session import Session
from app.models.user import User
from app.models.db import db
from app.utils.prompt.service_prompts import (
    SESSION_SUMMARY_SYSTEM_PROMPT,
    SESSION_SUMMARY_USER_PROMPT
)

@pytest.fixture(autouse=True)
def setup_teardown(app):
    """각 테스트 전후로 데이터베이스를 정리하는 fixture"""
    with app.app_context():
        yield
        db.session.rollback()
        Session.query.delete()
        User.query.delete()
        db.session.commit()

@pytest.fixture
def user_dao(app):
    """UserDAO 인스턴스를 생성하는 fixture"""
    with app.app_context():
        return UserDAO()

@pytest.fixture
def sample_user(user_dao):
    """테스트용 사용자를 생성하는 fixture"""
    user = user_dao.create(
        username="testuser",
        email="test@example.com"
    )
    db.session.refresh(user)
    return user

@pytest.fixture
def session_service(app):
    """SessionService 인스턴스를 생성하는 fixture"""
    with app.app_context():
        return SessionService()

@pytest.mark.run(order=4)  # DB 설정(1) -> 모델(2) -> DAO(3) -> Service(4) -> Route(5) -> DB 정리(6)
class TestSessionService:
    """SessionService 테스트 클래스"""

    def test_create_session_success(self, session_service, sample_user):
        """세션 생성 성공 테스트"""
        # When
        session = session_service.create_session(sample_user.id)
        
        # Then
        assert session['user_id'] == str(sample_user.id)
        assert session['start_at'] is not None
        assert session['finish_at'] is None
        assert 'id' in session
        assert isinstance(uuid.UUID(session['id']), uuid.UUID)

    def test_get_session_success(self, session_service, sample_user):
        """세션 조회 성공 테스트"""
        # Given
        created_session = session_service.create_session(sample_user.id)
        
        # When
        session = session_service.get_session(uuid.UUID(created_session['id']))
        
        # Then
        assert session is not None
        assert session['id'] == created_session['id']
        assert session['user_id'] == str(sample_user.id)

    def test_get_session_not_found(self, session_service):
        """존재하지 않는 세션 조회 테스트"""
        # When/Then
        with pytest.raises(ValueError, match="Session not found"):
            session_service.get_session(uuid.uuid4())

    def test_get_user_sessions(self, session_service, sample_user):
        """사용자의 모든 세션 조회 테스트"""
        # Given
        sessions = []
        for _ in range(3):
            session = session_service.create_session(sample_user.id)
            sessions.append(session)
        
        # When
        user_sessions = session_service.get_user_sessions(sample_user.id)
        
        # Then
        assert len(user_sessions) == len(sessions)
        for created_session in sessions:
            assert any(s['id'] == created_session['id'] for s in user_sessions)

    def test_update_session(self, session_service, sample_user):
        """세션 정보 업데이트 테스트"""
        # Given
        created_session = session_service.create_session(sample_user.id)
        new_title = "Updated Title"
        new_description = "Updated Description"
        
        # When
        updated_session = session_service.update_session(
            session_id=uuid.UUID(created_session['id']),
            title=new_title,
            description=new_description
        )
        
        # Then
        assert updated_session is not None
        assert updated_session['title'] == new_title
        assert updated_session['description'] == new_description
        assert updated_session['id'] == created_session['id']

    def test_update_session_not_found(self, session_service):
        """존재하지 않는 세션 업데이트 시도 테스트"""
        # When/Then
        with pytest.raises(ValueError, match="Session not found"):
            session_service.update_session(
                session_id=uuid.uuid4(),
                title="New Title"
            )

    def test_finish_session_success(self, session_service, sample_user):
        """세션 종료 성공 테스트"""
        # Given
        created_session = session_service.create_session(sample_user.id)
        
        # When
        finished_session = session_service.finish_session(uuid.UUID(created_session['id']))
        
        # Then
        assert finished_session is not None
        assert finished_session['finish_at'] is not None
        assert finished_session['id'] == created_session['id']

    def test_finish_session_not_found(self, session_service):
        """존재하지 않는 세션 종료 시도 테스트"""
        # When/Then
        with pytest.raises(ValueError, match="Session not found"):
            session_service.finish_session(uuid.uuid4())

    def test_finish_session_already_finished(self, session_service, sample_user):
        """이미 종료된 세션 종료 시도 테스트"""
        # Given
        created_session = session_service.create_session(sample_user.id)
        session_service.finish_session(uuid.UUID(created_session['id']))
        
        # When/Then
        with pytest.raises(ValueError, match="Session is already finished"):
            session_service.finish_session(uuid.UUID(created_session['id']))

    def test_delete_session_success(self, session_service, sample_user):
        """세션 삭제 성공 테스트"""
        # Given
        created_session = session_service.create_session(sample_user.id)
        
        # When
        result = session_service.delete_session(uuid.UUID(created_session['id']))
        
        # Then
        assert result is True
        with pytest.raises(ValueError, match="Session not found"):
            session_service.get_session(uuid.UUID(created_session['id']))

    def test_delete_session_not_found(self, session_service):
        """존재하지 않는 세션 삭제 시도 테스트"""
        # When
        result = session_service.delete_session(uuid.uuid4())
        
        # Then
        assert result is False

    def test_update_session_summary_success(self, session_service, sample_user):
        """세션 요약 업데이트 성공 테스트"""
        # Given
        created_session = session_service.create_session(sample_user.id)
        context_messages = [
            {"role": "system", "content": SESSION_SUMMARY_SYSTEM_PROMPT},
            {"role": "user", "content": SESSION_SUMMARY_USER_PROMPT + 
             "user: 테스트 메시지입니다.\n"
             "assistant: 테스트 응답입니다."}
        ]
        
        # When
        session_service.update_session_summary(
            session_id=uuid.UUID(created_session['id']),
            context_messages=context_messages
        )
        
        # Then
        updated_session = session_service.get_session(uuid.UUID(created_session['id']))
        assert updated_session['title'] is not None
        assert updated_session['description'] is not None

    def test_update_session_summary_not_found(self, session_service):
        """존재하지 않는 세션 요약 업데이트 시도 테스트"""
        # Given
        context_messages = [
            {"role": "system", "content": SESSION_SUMMARY_SYSTEM_PROMPT},
            {"role": "user", "content": SESSION_SUMMARY_USER_PROMPT + 
             "user: 테스트 메시지입니다.\n"
             "assistant: 테스트 응답입니다."}
        ]
        
        # When/Then
        with pytest.raises(ValueError, match="Session not found"):
            session_service.update_session_summary(
                session_id=uuid.uuid4(),
                context_messages=context_messages
            ) 