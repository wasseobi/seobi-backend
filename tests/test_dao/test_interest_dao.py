import pytest
from datetime import datetime, timezone, timedelta
import uuid

from app.dao.interest_dao import InterestDAO
from app.dao.user_dao import UserDAO
from app.models.interest import Interest
from app.models.user import User
from app.models.db import db


@pytest.fixture(autouse=True)
def setup_teardown(app):
    """각 테스트 전후로 데이터베이스를 정리하는 fixture"""
    with app.app_context():
        yield
        db.session.rollback()
        Interest.query.delete()
        User.query.delete()
        db.session.commit()


@pytest.fixture
def interest_dao(app):
    """InterestDAO 인스턴스를 생성하는 fixture"""
    with app.app_context():
        return InterestDAO()


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
def sample_interest(interest_dao, sample_user):
    """테스트용 관심사를 생성하는 fixture"""
    return interest_dao.create(
        user_id=sample_user.id,
        content="Test interest",
        source_message={"message_ids": [str(uuid.uuid4())]},
        importance=0.7
    )


# DB 설정(1) -> 모델(2) -> DAO(3) -> Service(4) -> Route(5) -> DB 정리(6)
@pytest.mark.run(order=3)
class TestInterestDAO:
    """InterestDAO 테스트 클래스"""

    def test_create_interest(self, interest_dao, sample_user):
        """관심사 생성 테스트"""
        # Given
        content = "New interest"
        source_message = {"message_ids": [str(uuid.uuid4())]}
        importance = 0.8

        # When
        interest = interest_dao.create(
            user_id=sample_user.id,
            content=content,
            source_message=source_message,
            importance=importance
        )

        # Then
        assert interest is not None
        assert interest.id is not None
        assert interest.user_id == sample_user.id
        assert interest.content == content
        assert interest.source_message == source_message
        assert interest.importance == importance
        assert isinstance(interest.id, uuid.UUID)
        assert isinstance(interest.created_at, datetime)
        assert interest.created_at.tzinfo == timezone.utc

    def test_get_by_id(self, interest_dao, sample_interest):
        """ID로 관심사 조회 테스트"""
        # When
        found_interest = interest_dao.get(sample_interest.id)

        # Then
        assert found_interest is not None
        assert found_interest.id == sample_interest.id
        assert found_interest.content == sample_interest.content
        assert found_interest.importance == sample_interest.importance

    def test_get_nonexistent_interest(self, interest_dao):
        """존재하지 않는 ID로 관심사 조회 테스트"""
        # When
        interest = interest_dao.get(uuid.uuid4())

        # Then
        assert interest is None

    def test_get_all_by_user_id(self, interest_dao, sample_user):
        """사용자의 모든 관심사 조회 테스트"""
        # Given
        interest1 = interest_dao.create(
            user_id=sample_user.id,
            content="Interest 1",
            source_message={"message_ids": [str(uuid.uuid4())]},
            importance=0.5,
            created_at=datetime.now(timezone.utc)
        )
        interest2 = interest_dao.create(
            user_id=sample_user.id,
            content="Interest 2",
            source_message={"message_ids": [str(uuid.uuid4())]},
            importance=0.7
        )
        interest3 = interest_dao.create(
            user_id=sample_user.id,
            content="Interest 3",
            source_message={"message_ids": [str(uuid.uuid4())]},
            importance=0.9,
            created_at=datetime.now(timezone.utc) + timedelta(days=1)
        )

        # When
        interests = interest_dao.get_all_by_user_id(sample_user.id)

        # Then
        assert len(interests) == 3
        assert all(i.user_id == sample_user.id for i in interests)

    def test_get_all_by_user_id_date_range(self, interest_dao, sample_user):
        """특정 기간 내 사용자의 관심사 조회 테스트"""
        # Given
        now = datetime.now(timezone.utc)
        yesterday = now - timedelta(days=1)
        tomorrow = now + timedelta(days=1)

        interest1 = interest_dao.create(
            user_id=sample_user.id,
            content="Interest 1",
            source_message={"message_ids": [str(uuid.uuid4())]},
            importance=0.5,
            created_at=datetime.now(timezone.utc)
        )

        # When
        interests = interest_dao.get_all_by_user_id_date_range(
            user_id=sample_user.id,
            start=yesterday,
            end=tomorrow
        )

        # Then
        assert len(interests) == 1
        assert interests[0].id == interest1.id
        assert interests[0].created_at > yesterday
        assert interests[0].created_at < tomorrow

    def test_interest_limit_per_user(self, interest_dao, sample_user):
        """사용자당 관심사 개수 제한 테스트 (200개)"""
        # Given
        # 201개의 관심사 생성
        interests = []
        for i in range(201):
            interest = interest_dao.create(
                user_id=sample_user.id,
                content=f"Interest {i}",
                source_message={"message_ids": [str(uuid.uuid4())]},
                importance=0.5,
                created_at=datetime.now(timezone.utc)
            )
            interests.append(interest)

        # When
        user_interests = interest_dao.get_all_by_user_id(sample_user.id)

        # Then
        assert len(user_interests) == 200  # 최대 200개만 유지
        # 가장 최근 200개가 유지되었는지 확인
        assert all(i.id in [interest.id for interest in interests[-200:]]
                   for i in user_interests)

    def test_update_interest(self, interest_dao, sample_interest):
        """관심사 업데이트 테스트"""
        # Given
        new_content = "Updated interest"
        new_importance = 0.9

        # When
        updated_interest = interest_dao.update(
            interest_id=sample_interest.id,
            content=new_content,
            importance=new_importance,
        )

        # Then
        assert updated_interest is not None
        assert updated_interest.id == sample_interest.id
        assert updated_interest.content == new_content
        assert updated_interest.importance == new_importance

    def test_get_all(self, interest_dao, sample_user):
        """get_all() 메서드 테스트"""
        # Given
        now = datetime.now(timezone.utc)
        interest1 = interest_dao.create(
            user_id=sample_user.id,
            content="Interest 1",
            source_message={"message_ids": [str(uuid.uuid4())]},
            importance=0.5,
            created_at=datetime.now(timezone.utc)
        )
        interest2 = interest_dao.create(
            user_id=sample_user.id,
            content="Interest 2",
            source_message={"message_ids": [str(uuid.uuid4())]},
            importance=0.7,
            created_at=datetime.now(timezone.utc)
        )

        # When
        interests = interest_dao.get_all()

        # Then
        assert len(interests) >= 2
        # created_at 기준 오름차순 정렬 확인
        assert interests[0].created_at <= interests[1].created_at
        interest_ids = {i.id for i in interests}
        assert interest1.id in interest_ids
        assert interest2.id in interest_ids

    def test_update_nonexistent_interest(self, interest_dao):
        """존재하지 않는 관심사 업데이트 테스트"""
        # When
        updated_interest = interest_dao.update(
            interest_id=uuid.uuid4(),
            content="New content"
        )

        # Then
        assert updated_interest is None

    def test_delete_interest(self, interest_dao, sample_interest):
        """관심사 삭제 테스트"""
        # When
        result = interest_dao.delete(sample_interest.id)

        # Then
        assert result is True
        deleted_interest = interest_dao.get(sample_interest.id)
        assert deleted_interest is None

    def test_delete_nonexistent_interest(self, interest_dao):
        """존재하지 않는 관심사 삭제 테스트"""
        # When
        result = interest_dao.delete(uuid.uuid4())

        # Then
        assert result is False

    def test_get_empty_user_interests(self, interest_dao, sample_user):
        """관심사가 없는 사용자의 관심사 조회 테스트"""
        # When
        interests = interest_dao.get_all_by_user_id(sample_user.id)

        # Then
        assert len(interests) == 0

    def test_update_interest_partial(self, interest_dao, sample_interest):
        """관심사 부분 업데이트 테스트"""
        # Given
        original_content = sample_interest.content
        new_importance = 0.9

        # When
        updated_interest = interest_dao.update(
            interest_id=sample_interest.id,
            importance=new_importance
        )

        # Then
        assert updated_interest is not None
        assert updated_interest.id == sample_interest.id
        assert updated_interest.content == original_content  # content는 변경되지 않아야 함
        assert updated_interest.importance == new_importance
