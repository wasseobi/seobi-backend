import pytest
from app.dao.user_dao import UserDAO
from app.models.user import User
from app.models.db import db
import uuid

@pytest.fixture(autouse=True)
def setup_teardown(app):
    """각 테스트 전후로 데이터베이스를 정리하는 fixture"""
    with app.app_context():
        yield
        db.session.rollback()
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
    return user_dao.create(
        username="testuser",
        email="test@example.com"
    )

@pytest.mark.run(order=3)  # DB 설정(1) -> 모델(2) -> DAO(3) -> Service(4) -> Route(5) -> DB 정리(6)
class TestUserDAO:
    """UserDAO 테스트 클래스"""

    # BaseDAO에서 상속받은 메서드 테스트
    def test_get_by_id(self, user_dao, sample_user):
        """BaseDAO.get() 메서드 테스트"""
        # When
        found_user = user_dao.get(str(sample_user.id))

        # Then
        assert found_user is not None
        assert found_user.id == sample_user.id
        assert found_user.username == sample_user.username
        assert found_user.email == sample_user.email

    def test_get_nonexistent_by_id(self, user_dao):
        """존재하지 않는 ID로 get() 메서드 테스트"""
        # When
        user = user_dao.get(str(uuid.uuid4()))

        # Then
        assert user is None

    def test_get_all_users(self, user_dao):
        """BaseDAO.get_all() 메서드 테스트"""
        # Given
        user1 = user_dao.create(username="user1", email="user1@example.com")
        user2 = user_dao.create(username="user2", email="user2@example.com")
        user3 = user_dao.create(username="user3", email="user3@example.com")

        # When
        users = user_dao.get_all()

        # Then
        assert len(users) >= 3  # 다른 테스트에서 생성된 사용자가 있을 수 있음
        user_ids = {u.id for u in users}
        assert user1.id in user_ids
        assert user2.id in user_ids
        assert user3.id in user_ids

    def test_delete_user(self, user_dao, sample_user):
        """BaseDAO.delete() 메서드 테스트"""
        # When
        result = user_dao.delete(str(sample_user.id))

        # Then
        assert result is True
        deleted_user = user_dao.get(str(sample_user.id))
        assert deleted_user is None

    def test_delete_nonexistent_user(self, user_dao):
        """존재하지 않는 ID로 delete() 메서드 테스트"""
        # When
        result = user_dao.delete(str(uuid.uuid4()))

        # Then
        assert result is False

    def test_query_method(self, user_dao):
        """BaseDAO.query() 메서드 테스트"""
        # When
        query = user_dao.query()

        # Then
        assert query is not None
        # query 객체가 SQLAlchemy Query 인스턴스인지 확인
        assert hasattr(query, 'filter')
        assert hasattr(query, 'filter_by')
        assert hasattr(query, 'all')

    # UserDAO 고유 메서드 테스트
    def test_get_by_email(self, user_dao, sample_user):
        """이메일로 사용자 조회 테스트"""
        # When
        found_user = user_dao.get_by_email(sample_user.email)

        # Then
        assert found_user is not None
        assert found_user.id == sample_user.id
        assert found_user.email == sample_user.email

    def test_get_by_username(self, user_dao, sample_user):
        """사용자명으로 사용자 조회 테스트"""
        # When
        found_user = user_dao.get_by_username(sample_user.username)

        # Then
        assert found_user is not None
        assert found_user.id == sample_user.id
        assert found_user.username == sample_user.username

    def test_create_user(self, user_dao):
        """사용자 생성 테스트"""
        # Given
        username = "newuser"
        email = "newuser@example.com"

        # When
        user = user_dao.create(username=username, email=email)

        # Then
        assert user is not None
        assert user.id is not None
        assert user.username == username
        assert user.email == email
        assert isinstance(user.id, uuid.UUID)

    def test_update_user(self, user_dao, sample_user):
        """사용자 정보 업데이트 테스트"""
        # Given
        new_username = "updateduser"
        new_email = "updated@example.com"

        # When
        updated_user = user_dao.update(
            sample_user.id,
            username=new_username,
            email=new_email
        )

        # Then
        assert updated_user is not None
        assert updated_user.id == sample_user.id
        assert updated_user.username == new_username
        assert updated_user.email == new_email

    def test_update_user_partial(self, user_dao, sample_user):
        """사용자 정보 부분 업데이트 테스트"""
        # Given
        original_email = sample_user.email
        new_username = "partialupdate"

        # When
        updated_user = user_dao.update(
            sample_user.id,
            username=new_username
        )

        # Then
        assert updated_user is not None
        assert updated_user.id == sample_user.id
        assert updated_user.username == new_username
        assert updated_user.email == original_email  # email은 변경되지 않아야 함

    def test_get_by_nonexistent_email(self, user_dao):
        """존재하지 않는 이메일로 사용자 조회 테스트"""
        # When
        user = user_dao.get_by_email("nonexistent@example.com")

        # Then
        assert user is None

    def test_get_by_nonexistent_username(self, user_dao):
        """존재하지 않는 사용자명으로 사용자 조회 테스트"""
        # When
        user = user_dao.get_by_username("nonexistentuser")

        # Then
        assert user is None

    def test_create_duplicate_email(self, user_dao, sample_user):
        """중복 이메일로 사용자 생성 시도 테스트"""
        # Given
        duplicate_email = sample_user.email
        new_username = "anotheruser"

        # When/Then
        with pytest.raises(Exception):  # 구체적인 예외 타입은 실제 구현에 따라 달라질 수 있음
            user_dao.create(username=new_username, email=duplicate_email)

    def test_create_duplicate_username(self, user_dao, sample_user):
        """중복 사용자명으로 사용자 생성 시도 테스트"""
        # Given
        duplicate_username = sample_user.username
        new_email = "another@example.com"

        # When/Then
        with pytest.raises(Exception):  # 구체적인 예외 타입은 실제 구현에 따라 달라질 수 있음
            user_dao.create(username=duplicate_username, email=new_email)

    def test_update_user_memory(self, user_dao, sample_user):
        """사용자 메모리 업데이트 테스트"""
        # Given
        new_memory = {
            "last_login": "2024-03-20",
            "preferences": {
                "theme": "dark",
                "notifications": True
            }
        }

        # When
        updated_user = user_dao.update_user_memory(sample_user.id, new_memory)

        # Then
        assert updated_user is not None
        assert updated_user.id == sample_user.id
        assert updated_user.user_memory == new_memory
        # 다른 필드들은 변경되지 않았는지 확인
        assert updated_user.username == sample_user.username
        assert updated_user.email == sample_user.email

    def test_update_user_memory_to_null(self, user_dao, sample_user):
        """사용자 메모리를 null로 업데이트 테스트"""
        # Given
        # 먼저 user_memory를 설정
        initial_memory = {"test": "data"}
        user_dao.update_user_memory(sample_user.id, initial_memory)
        
        # When
        updated_user = user_dao.update_user_memory(sample_user.id, None)

        # Then
        assert updated_user is not None
        assert updated_user.id == sample_user.id
        assert updated_user.user_memory is None
        # 다른 필드들은 변경되지 않았는지 확인
        assert updated_user.username == sample_user.username
        assert updated_user.email == sample_user.email

    def test_update_user_memory_nonexistent_user(self, user_dao):
        """존재하지 않는 사용자의 메모리 업데이트 시도 테스트"""
        # Given
        nonexistent_id = uuid.uuid4()
        test_memory = {"test": "data"}

        # When
        updated_user = user_dao.update_user_memory(nonexistent_id, test_memory)

        # Then
        assert updated_user is None 