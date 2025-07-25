import uuid
import pytest
from app.services.user_service import UserService
from app.models.user import User
from app.models.db import db

@pytest.fixture(autouse=True)
def setup_teardown(app):
    """각 테스트 전후로 데이터베이스를 정리하는 fixture"""
    with app.app_context():
        yield
        db.session.rollback()
        User.query.delete()
        db.session.commit()

@pytest.fixture
def user_service(app):
    """UserService 인스턴스를 생성하는 fixture"""
    with app.app_context():
        return UserService()

@pytest.fixture
def sample_user_data():
    """테스트용 사용자 데이터를 제공하는 fixture"""
    return {
        'username': 'testuser',
        'email': 'test@example.com'
    }

@pytest.mark.run(order=4)  # DB 설정(1) -> 모델(2) -> DAO(3) -> Service(4) -> Route(5) -> DB 정리(6)
class TestUserService:
    """UserService 테스트 클래스"""

    def test_create_user_success(self, user_service, sample_user_data):
        """사용자 생성 성공 테스트"""
        # When
        user = user_service.create_user(
            username=sample_user_data['username'],
            email=sample_user_data['email']
        )
        
        # Then
        assert user['username'] == sample_user_data['username']
        assert user['email'] == sample_user_data['email']
        assert 'id' in user
        assert isinstance(uuid.UUID(user['id']), uuid.UUID)

    def test_create_user_duplicate_email(self, user_service, sample_user_data):
        """중복 이메일로 사용자 생성 시도 테스트"""
        # Given
        user_service.create_user(
            username=sample_user_data['username'],
            email=sample_user_data['email']
        )
        
        # When/Then
        with pytest.raises(ValueError, match="User with this email already exists"):
            user_service.create_user(
                username='anotheruser',
                email=sample_user_data['email']
            )

    def test_create_user_duplicate_username(self, user_service, sample_user_data):
        """중복 사용자명으로 사용자 생성 시도 테스트"""
        # Given
        user_service.create_user(
            username=sample_user_data['username'],
            email=sample_user_data['email']
        )
        
        # When/Then
        with pytest.raises(ValueError, match="User with this username already exists"):
            user_service.create_user(
                username=sample_user_data['username'],
                email='another@example.com'
            )

    def test_get_user_by_id(self, user_service, sample_user_data):
        """ID로 사용자 조회 테스트"""
        # Given
        created_user = user_service.create_user(
            username=sample_user_data['username'],
            email=sample_user_data['email']
        )
        
        # When
        user = user_service.get_user_by_id(uuid.UUID(created_user['id']))
        
        # Then
        assert user is not None
        assert user['username'] == sample_user_data['username']
        assert user['email'] == sample_user_data['email']
        assert user['id'] == created_user['id']

    def test_get_user_by_id_not_found(self, user_service):
        """존재하지 않는 ID로 사용자 조회 테스트"""
        # When
        user = user_service.get_user_by_id(uuid.uuid4())
        
        # Then
        assert user is None

    def test_get_user_by_email(self, user_service, sample_user_data):
        """이메일로 사용자 조회 테스트"""
        # Given
        created_user = user_service.create_user(
            username=sample_user_data['username'],
            email=sample_user_data['email']
        )
        
        # When
        user = user_service.get_user_by_email(sample_user_data['email'])
        
        # Then
        assert user is not None
        assert user['username'] == sample_user_data['username']
        assert user['email'] == sample_user_data['email']
        assert user['id'] == created_user['id']

    def test_get_user_by_email_not_found(self, user_service):
        """존재하지 않는 이메일로 사용자 조회 테스트"""
        # When
        user = user_service.get_user_by_email('nonexistent@example.com')
        
        # Then
        assert user is None

    def test_get_user_by_username(self, user_service, sample_user_data):
        """사용자명으로 사용자 조회 테스트"""
        # Given
        created_user = user_service.create_user(
            username=sample_user_data['username'],
            email=sample_user_data['email']
        )
        
        # When
        user = user_service.get_user_by_username(sample_user_data['username'])
        
        # Then
        assert user is not None
        assert user['username'] == sample_user_data['username']
        assert user['email'] == sample_user_data['email']
        assert user['id'] == created_user['id']

    def test_get_user_by_username_not_found(self, user_service):
        """존재하지 않는 사용자명으로 사용자 조회 테스트"""
        # When
        user = user_service.get_user_by_username('nonexistentuser')
        
        # Then
        assert user is None

    def test_update_user(self, user_service, sample_user_data):
        """사용자 정보 업데이트 테스트"""
        # Given
        created_user = user_service.create_user(
            username=sample_user_data['username'],
            email=sample_user_data['email']
        )
        new_username = 'updateduser'
        new_email = 'updated@example.com'
        
        # When
        updated_user = user_service.update_user(
            user_id=uuid.UUID(created_user['id']),
            username=new_username,
            email=new_email
        )
        
        # Then
        assert updated_user is not None
        assert updated_user['username'] == new_username
        assert updated_user['email'] == new_email
        assert updated_user['id'] == created_user['id']

    def test_update_user_not_found(self, user_service):
        """존재하지 않는 사용자 정보 업데이트 시도 테스트"""
        # When
        updated_user = user_service.update_user(
            user_id=uuid.uuid4(),
            username='newuser',
            email='new@example.com'
        )
        
        # Then
        assert updated_user is None

    def test_update_user_duplicate_email(self, user_service, sample_user_data):
        """중복 이메일로 사용자 정보 업데이트 시도 테스트"""
        # Given
        user1 = user_service.create_user(
            username='user1',
            email='user1@example.com'
        )
        user_service.create_user(
            username='user2',
            email='user2@example.com'
        )
        
        # When/Then
        with pytest.raises(ValueError, match="Email already in use"):
            user_service.update_user(
                user_id=uuid.UUID(user1['id']),
                email='user2@example.com'
            )

    def test_update_user_duplicate_username(self, user_service, sample_user_data):
        """중복 사용자명으로 사용자 정보 업데이트 시도 테스트"""
        # Given
        user1 = user_service.create_user(
            username='user1',
            email='user1@example.com'
        )
        user_service.create_user(
            username='user2',
            email='user2@example.com'
        )
        
        # When/Then
        with pytest.raises(ValueError, match="Username already in use"):
            user_service.update_user(
                user_id=uuid.UUID(user1['id']),
                username='user2'
            )

    def test_delete_user(self, user_service, sample_user_data):
        """사용자 삭제 테스트"""
        # Given
        created_user = user_service.create_user(
            username=sample_user_data['username'],
            email=sample_user_data['email']
        )
        
        # When
        result = user_service.delete_user(uuid.UUID(created_user['id']))
        
        # Then
        assert result is True
        user = user_service.get_user_by_id(uuid.UUID(created_user['id']))
        assert user is None

    def test_delete_user_not_found(self, user_service):
        """존재하지 않는 사용자 삭제 시도 테스트"""
        # When
        result = user_service.delete_user(uuid.uuid4())
        
        # Then
        assert result is False

    def test_get_all_users(self, user_service, sample_user_data):
        """모든 사용자 조회 테스트"""
        # Given
        users = []
        for i in range(3):
            user = user_service.create_user(
                username=f"{sample_user_data['username']}{i}",
                email=f"user{i}@example.com"
            )
            users.append(user)
        
        # When
        all_users = user_service.get_all_users()
        
        # Then
        assert len(all_users) >= len(users)
        for created_user in users:
            assert any(u['id'] == created_user['id'] for u in all_users)

    def test_update_user_memory_with_llm(self, user_service, sample_user_data):
        """사용자 메모리 업데이트 테스트"""
        # Given
        created_user = user_service.create_user(
            username=sample_user_data['username'],
            email=sample_user_data['email']
        )
        summary = "테스트 요약"
        messages = [{"role": "user", "content": "테스트 메시지"}]
        
        # When
        updated_user = user_service.update_user_memory_with_llm(
            user_id=created_user['id'],
            summary=summary,
            messages=messages
        )
        
        # Then
        assert updated_user is not None
        assert isinstance(updated_user, User)

    def test_initialize_agent_state(self, user_service, sample_user_data):
        """에이전트 상태 초기화 테스트"""
        # Given
        created_user = user_service.create_user(
            username=sample_user_data['username'],
            email=sample_user_data['email']
        )
        
        # When
        agent_state = user_service.initialize_agent_state(created_user['id'])
        
        # Then
        assert agent_state is not None
        assert isinstance(agent_state, dict)

        # 이전 상태에서 유지할 항목들 검증
        assert 'messages' in agent_state
        assert isinstance(agent_state['messages'], list)
        assert 'summary' in agent_state
        assert 'user_memory' in agent_state

        # 사용자 관련 정보 검증
        assert agent_state['user_id'] == created_user['id']
        assert 'user_location' in agent_state
        assert agent_state['user_location'] is None

        # 매 대화마다 초기화되는 항목들 검증
        assert agent_state['current_input'] == ""
        assert agent_state['scratchpad'] == []
        assert agent_state['next_step'] is None
        assert agent_state['step_count'] == 0
        assert agent_state['tool_results'] is None
        assert agent_state['current_tool_call_id'] is None
        assert agent_state['current_tool_name'] is None
        assert agent_state['current_tool_calls'] is None

    def test_save_user_memory_from_state(self, user_service, sample_user_data):
        """에이전트 상태에서 사용자 메모리 저장 테스트"""
        # Given
        created_user = user_service.create_user(
            username=sample_user_data['username'],
            email=sample_user_data['email']
        )
        agent_state = {
            "messages": [{"role": "user", "content": "테스트 메시지"}],
            "summary": "테스트 요약",
            "user_memory": "기존 메모리",
            "user_id": created_user['id']
        }
        
        # When
        updated_user = user_service.save_user_memory_from_state(
            user_id=created_user['id'],
            agent_state=agent_state
        )
        
        # Then
        assert updated_user is not None
        assert isinstance(updated_user, User)

    def test_update_user_memory_with_llm_no_previous_memory(self, user_service, sample_user_data):
        """이전 메모리가 없는 경우의 사용자 메모리 업데이트 테스트"""
        # Given
        created_user = user_service.create_user(
            username=sample_user_data['username'],
            email=sample_user_data['email']
        )
        summary = "새로운 요약"
        messages = [{"role": "user", "content": "새로운 메시지"}]
        
        # When
        updated_user = user_service.update_user_memory_with_llm(
            user_id=created_user['id'],
            summary=summary,
            messages=messages
        )
        
        # Then
        assert updated_user is not None
        assert isinstance(updated_user, User)

    def test_update_user_memory_with_llm_with_none_summary(self, user_service, sample_user_data):
        """요약이 None인 경우의 사용자 메모리 업데이트 테스트"""
        # Given
        created_user = user_service.create_user(
            username=sample_user_data['username'],
            email=sample_user_data['email']
        )
        messages = [{"role": "user", "content": "테스트 메시지"}]
        
        # When
        updated_user = user_service.update_user_memory_with_llm(
            user_id=created_user['id'],
            summary=None,
            messages=messages
        )
        
        # Then
        assert updated_user is not None
        assert isinstance(updated_user, User)

    def test_save_user_memory_from_empty_state(self, user_service, sample_user_data):
        """빈 상태에서 사용자 메모리 저장 테스트"""
        # Given
        created_user = user_service.create_user(
            username=sample_user_data['username'],
            email=sample_user_data['email']
        )
        empty_state = {
            "messages": [],
            "summary": None,
            "user_memory": None,
            "user_id": created_user['id']
        }
        
        # When
        updated_user = user_service.save_user_memory_from_state(
            user_id=created_user['id'],
            agent_state=empty_state
        )
        
        # Then
        assert updated_user is not None
        assert isinstance(updated_user, User)