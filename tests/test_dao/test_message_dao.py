import pytest
from app.dao.message_dao import MessageDAO
from app.dao.session_dao import SessionDAO
from app.dao.user_dao import UserDAO
from app.models.message import Message
from app.models.session import Session
from app.models.user import User
from app.models.db import db
from datetime import datetime, timezone, timedelta
import uuid
import numpy as np

def create_test_vector(dim=1536):
    """테스트용 벡터 생성 (기본값 1536차원)"""
    return np.random.rand(dim).astype(np.float32)

@pytest.fixture(autouse=True)
def setup_teardown(app):
    """각 테스트 전후로 데이터베이스를 정리하는 fixture"""
    with app.app_context():
        yield
        db.session.rollback()
        Message.query.delete()
        Session.query.delete()
        User.query.delete()
        db.session.commit()

@pytest.fixture
def message_dao(app):
    """MessageDAO 인스턴스를 생성하는 fixture"""
    with app.app_context():
        return MessageDAO()

@pytest.fixture
def session_dao(app):
    """SessionDAO 인스턴스를 생성하는 fixture"""
    with app.app_context():
        return SessionDAO()

@pytest.fixture
def user_dao(app):
    """UserDAO 인스턴스를 생성하는 fixture"""
    with app.app_context():
        return UserDAO()

@pytest.fixture
def sample_user(user_dao):
    """테스트용 사용자를 생성하는 fixture"""
    return user_dao.create(
        username="testuser",
        email="test@example.com"
    )

@pytest.fixture
def sample_session(session_dao, sample_user):
    """테스트용 세션을 생성하는 fixture"""
    return session_dao.create(user_id=sample_user.id)

@pytest.fixture
def sample_message(message_dao, sample_session, sample_user):
    """테스트용 메시지를 생성하는 fixture"""
    return message_dao.create(
        session_id=sample_session.id,
        user_id=sample_user.id,
        content="Test message",
        role="user"
    )

@pytest.mark.run(order=3)  # DB 설정(1) -> 모델(2) -> DAO(3) -> Service(4) -> Route(5) -> DB 정리(6)
class TestMessageDAO:
    """MessageDAO 테스트 클래스"""

    def test_create_message(self, message_dao, sample_session, sample_user):
        """메시지 생성 테스트"""
        # Given
        content = "Hello, world!"
        role = "user"
        vector = create_test_vector()  # 1536차원 벡터 생성
        metadata = {"key": "value"}

        # When
        message = message_dao.create(
            session_id=sample_session.id,
            user_id=sample_user.id,
            content=content,
            role=role,
            vector=vector,
            metadata=metadata
        )

        # Then
        assert message is not None
        assert message.id is not None
        assert message.session_id == sample_session.id
        assert message.user_id == sample_user.id
        assert message.content == content
        assert message.role == role
        assert message.vector is not None
        assert len(message.vector) == 1536  # 벡터 차원 확인
        assert message.message_metadata == metadata
        assert isinstance(message.id, uuid.UUID)
        assert isinstance(message.timestamp, datetime)

    def test_get_message_by_id(self, message_dao, sample_message):
        """ID로 메시지 조회 테스트"""
        # When
        found_message = message_dao.get_all_by_id(sample_message.id)

        # Then
        assert found_message is not None
        assert found_message.id == sample_message.id
        assert found_message.content == sample_message.content
        assert found_message.role == sample_message.role

    def test_get_nonexistent_message(self, message_dao):
        """존재하지 않는 ID로 메시지 조회 테스트"""
        # When
        message = message_dao.get_all_by_id(uuid.uuid4())

        # Then
        assert message is None

    def test_get_all_by_user_id(self, message_dao, sample_user, sample_session):
        """사용자의 모든 메시지 조회 테스트"""
        # Given
        # 여러 개의 메시지 생성
        message1 = message_dao.create(
            session_id=sample_session.id,
            user_id=sample_user.id,
            content="Message 1",
            role="user"
        )
        message2 = message_dao.create(
            session_id=sample_session.id,
            user_id=sample_user.id,
            content="Message 2",
            role="assistant"
        )
        message3 = message_dao.create(
            session_id=sample_session.id,
            user_id=sample_user.id,
            content="Message 3",
            role="user"
        )

        # When
        messages = message_dao.get_all_by_user_id(sample_user.id)

        # Then
        assert len(messages) == 3
        assert all(m.user_id == sample_user.id for m in messages)
        # 타임스탬프 기준 내림차순 정렬 확인
        assert messages[0].timestamp >= messages[1].timestamp >= messages[2].timestamp

    def test_get_user_messages_empty(self, message_dao, sample_user):
        """메시지가 없는 사용자의 메시지 조회 테스트"""
        # When
        messages = message_dao.get_all_by_user_id(sample_user.id)

        # Then
        assert len(messages) == 0

    def test_get_all_by_session_id(self, message_dao, sample_session, sample_user):
        """세션의 모든 메시지 조회 테스트"""
        # Given
        # 여러 개의 메시지 생성
        message1 = message_dao.create(
            session_id=sample_session.id,
            user_id=sample_user.id,
            content="Message 1",
            role="user"
        )
        message2 = message_dao.create(
            session_id=sample_session.id,
            user_id=sample_user.id,
            content="Message 2",
            role="assistant"
        )
        message3 = message_dao.create(
            session_id=sample_session.id,
            user_id=sample_user.id,
            content="Message 3",
            role="user"
        )

        # When
        messages = message_dao.get_all_by_session_id(sample_session.id)

        # Then
        assert len(messages) == 3
        assert all(m.session_id == sample_session.id for m in messages)
        # 타임스탬프 기준 오름차순 정렬 확인
        assert messages[0].timestamp <= messages[1].timestamp <= messages[2].timestamp

    def test_get_session_messages_empty(self, message_dao, sample_session):
        """메시지가 없는 세션의 메시지 조회 테스트"""
        # When
        messages = message_dao.get_all_by_session_id(sample_session.id)

        # Then
        assert len(messages) == 0

    def test_update_message(self, message_dao, sample_message):
        """메시지 업데이트 테스트"""
        # Given
        new_content = "Updated message"
        new_metadata = {"updated": True}

        # When
        updated_message = message_dao.update(
            message_id=sample_message.id,
            content=new_content,
            message_metadata=new_metadata
        )

        # Then
        assert updated_message is not None
        assert updated_message.id == sample_message.id
        assert updated_message.content == new_content
        assert updated_message.message_metadata == new_metadata

    def test_delete_message(self, message_dao, sample_message):
        """메시지 삭제 테스트"""
        # When
        result = message_dao.delete(sample_message.id)

        # Then
        assert result is True
        deleted_message = message_dao.get_all_by_id(sample_message.id)
        assert deleted_message is None

    def test_delete_nonexistent_message(self, message_dao):
        """존재하지 않는 메시지 삭제 테스트"""
        # When
        result = message_dao.delete(uuid.uuid4())

        # Then
        assert result is False

    def test_get_all_messages(self, message_dao, session_dao, sample_session, sample_user):
        """모든 메시지 조회 테스트"""
        # Given
        # 여러 사용자의 메시지 생성
        user2 = User(username="user2", email="user2@example.com")
        db.session.add(user2)
        db.session.commit()

        session2 = session_dao.create(user_id=user2.id)
        
        message1 = message_dao.create(
            session_id=sample_session.id,
            user_id=sample_user.id,
            content="Message 1",
            role="user",
            vector=create_test_vector()
        )
        message2 = message_dao.create(
            session_id=session2.id,
            user_id=user2.id,
            content="Message 2",
            role="user",
            vector=create_test_vector()
        )
        message3 = message_dao.create(
            session_id=sample_session.id,
            user_id=sample_user.id,
            content="Message 3",
            role="assistant",
            vector=create_test_vector()
        )

        # When
        messages = message_dao.get_all()

        # Then
        assert len(messages) == 3
        # 타임스탬프 기준 오름차순 정렬 확인
        assert messages[0].timestamp <= messages[1].timestamp <= messages[2].timestamp
        # 메시지 ID 목록 확인
        message_ids = {m.id for m in messages}
        assert message_ids == {message1.id, message2.id, message3.id} 