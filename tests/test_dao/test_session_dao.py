import pytest
from app.dao.session_dao import SessionDAO
from app.dao.user_dao import UserDAO
from app.models.session import Session
from app.models.user import User
from app.models.db import db
from datetime import datetime, timezone, timedelta
import uuid

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

@pytest.mark.run(order=3)  # DB 설정(1) -> 모델(2) -> DAO(3) -> Service(4) -> Route(5) -> DB 정리(6)
class TestSessionDAO:
    """SessionDAO 테스트 클래스"""

    # BaseDAO에서 상속받은 메서드 테스트
    def test_get_nonexistent_by_id(self, session_dao):
        """존재하지 않는 ID로 get() 메서드 테스트"""
        # When
        session = session_dao.get(str(uuid.uuid4()))

        # Then
        assert session is None

    def test_get_all_sessions(self, session_dao, sample_user):
        """BaseDAO.get_all() 메서드 테스트"""
        # Given
        session1 = session_dao.create(user_id=sample_user.id)
        session2 = session_dao.create(user_id=sample_user.id)
        session3 = session_dao.create(user_id=sample_user.id)

        # When
        sessions = session_dao.get_all()

        # Then
        assert len(sessions) >= 3  # 다른 테스트에서 생성된 세션이 있을 수 있음
        session_ids = {s.id for s in sessions}
        assert session1.id in session_ids
        assert session2.id in session_ids
        assert session3.id in session_ids

    def test_delete_session(self, session_dao, sample_session):
        """BaseDAO.delete() 메서드 테스트"""
        # When
        result = session_dao.delete(str(sample_session.id))

        # Then
        assert result is True
        deleted_session = session_dao.get(str(sample_session.id))
        assert deleted_session is None

    def test_delete_nonexistent_session(self, session_dao):
        """존재하지 않는 ID로 delete() 메서드 테스트"""
        # When
        result = session_dao.delete(str(uuid.uuid4()))

        # Then
        assert result is False

    def test_query_method(self, session_dao):
        """BaseDAO.query() 메서드 테스트"""
        # When
        query = session_dao.query()

        # Then
        assert query is not None
        # query 객체가 SQLAlchemy Query 인스턴스인지 확인
        assert hasattr(query, 'filter')
        assert hasattr(query, 'filter_by')
        assert hasattr(query, 'all')

    # SessionDAO 고유 메서드 테스트
    def test_get_by_id(self, session_dao, sample_session):
        """세션 ID로 조회 테스트"""
        # When
        found_session = session_dao.get_by_id(sample_session.id)

        # Then
        assert found_session is not None
        assert found_session.id == sample_session.id
        assert found_session.user_id == sample_session.user_id
        assert isinstance(found_session.start_at, datetime)

    def test_get_all_by_user_id(self, session_dao, sample_user):
        """사용자의 모든 세션 조회 테스트"""
        # Given
        session1 = session_dao.create(user_id=sample_user.id)
        session2 = session_dao.create(user_id=sample_user.id)
        session3 = session_dao.create(user_id=sample_user.id)

        # When
        sessions = session_dao.get_all_by_user_id(sample_user.id)

        # Then
        assert len(sessions) == 3
        assert all(s.user_id == sample_user.id for s in sessions)
        # 생성 시간 기준 내림차순 정렬 확인
        assert sessions[0].start_at >= sessions[1].start_at >= sessions[2].start_at

    def test_create_session(self, session_dao, sample_user):
        """세션 생성 테스트"""
        # When
        session = session_dao.create(user_id=sample_user.id)

        # Then
        assert session is not None
        assert session.id is not None
        assert session.user_id == sample_user.id
        assert isinstance(session.id, uuid.UUID)
        assert isinstance(session.start_at, datetime)
        assert session.start_at.tzinfo == timezone.utc  # UTC 시간대 확인

    def test_get_user_sessions_empty(self, session_dao, sample_user):
        """세션이 없는 사용자의 세션 조회 테스트"""
        # Given
        # sample_user의 세션을 모두 삭제
        Session.query.filter_by(user_id=sample_user.id).delete()
        db.session.commit()

        # When
        sessions = session_dao.get_all_by_user_id(sample_user.id)

        # Then
        assert len(sessions) == 0

    def test_get_nonexistent_user_sessions(self, session_dao):
        """존재하지 않는 사용자의 세션 조회 테스트"""
        # When
        sessions = session_dao.get_all_by_user_id(uuid.uuid4())

        # Then
        assert len(sessions) == 0

    def test_create_session_nonexistent_user(self, session_dao):
        """존재하지 않는 사용자로 세션 생성 시도 테스트"""
        # When/Then
        with pytest.raises(Exception):  # 구체적인 예외 타입은 실제 구현에 따라 달라질 수 있음
            session_dao.create(user_id=uuid.uuid4())

    def test_update_session(self, session_dao, sample_session):
        """BaseDAO.update() 메서드 테스트"""
        # Given
        new_finish_time = datetime.now(timezone.utc)
        new_metadata = {"key": "value"}

        # When
        updated_session = session_dao.update(
            sample_session.id,
            finish_at=new_finish_time,
            metadata=new_metadata
        )

        # Then
        assert updated_session is not None
        assert updated_session.id == sample_session.id
        assert updated_session.finish_at == new_finish_time
        assert updated_session.metadata == new_metadata

    def test_update_session_partial(self, session_dao, sample_session):
        """부분 update 테스트 (일부 필드만 업데이트)"""
        # Given
        original_finish_time = sample_session.finish_at
        new_metadata = {"updated": True}

        # When
        updated_session = session_dao.update(
            sample_session.id,
            metadata=new_metadata
        )

        # Then
        assert updated_session is not None
        assert updated_session.id == sample_session.id
        assert updated_session.metadata == new_metadata
        assert updated_session.finish_at == original_finish_time

    def test_update_finish_time(self, session_dao, sample_session):
        """update_finish_time 메서드 테스트"""
        # Given
        new_finish_time = datetime.now(timezone.utc)

        # When
        updated_session = session_dao.update_finish_time(
            sample_session.id,
            new_finish_time
        )

        # Then
        assert updated_session is not None
        assert updated_session.id == sample_session.id
        assert updated_session.finish_at == new_finish_time
        assert updated_session.finish_at.tzinfo == timezone.utc