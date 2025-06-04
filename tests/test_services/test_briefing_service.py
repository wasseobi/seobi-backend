import uuid
import pytest
from app.services.briefing_service import BriefingService
from app.dao.user_dao import UserDAO
from app.models.user import User
from app.models.briefing import Briefing
from app.models.db import db

@pytest.fixture(autouse=True)
def setup_teardown(app):
    """각 테스트 전후로 데이터베이스를 정리하는 fixture"""
    with app.app_context():
        yield
        db.session.rollback()
        Briefing.query.delete()
        User.query.delete()
        db.session.commit()

@pytest.fixture
def user_dao(app):
    with app.app_context():
        return UserDAO()

@pytest.fixture
def sample_user(user_dao):
    """테스트용 사용자를 생성하는 fixture (세션에 바인딩된 User 인스턴스 반환)"""
    user = user_dao.create(
        username="testuser",
        email="test@example.com"
    )
    db.session.refresh(user)
    return user

@pytest.fixture
def briefing_service(app):
    with app.app_context():
        return BriefingService()

@pytest.fixture
def sample_briefing(app, sample_user):
    with app.app_context():
        briefing = Briefing(user_id=sample_user.id, content="테스트 브리핑")
        db.session.add(briefing)
        db.session.commit()
        return briefing

@pytest.mark.run(order=4)
class TestBriefingService:
    """BriefingService 테스트 클래스"""
    def test_create_briefing(self, briefing_service, sample_user):
        """브리핑 생성 성공 테스트"""
        briefing = briefing_service.create_briefing(user_id=sample_user.id, content="새 브리핑")
        assert briefing['user_id'] == str(sample_user.id)
        assert briefing['content'] == "새 브리핑"
        assert 'id' in briefing
        assert isinstance(uuid.UUID(briefing['id']), uuid.UUID)

    def test_get_briefing(self, briefing_service, sample_user):
        """ID로 브리핑 조회 테스트"""
        created = briefing_service.create_briefing(user_id=sample_user.id, content="조회 테스트")
        found = briefing_service.get_briefing(uuid.UUID(created['id']))
        assert found['id'] == created['id']
        assert found['content'] == "조회 테스트"

    def test_get_briefing_not_found(self, briefing_service):
        """존재하지 않는 ID로 브리핑 조회 테스트"""
        with pytest.raises(ValueError):
            briefing_service.get_briefing(uuid.uuid4())

    def test_get_all_briefings(self, briefing_service, sample_user):
        """모든 브리핑 조회 테스트"""
        b1 = briefing_service.create_briefing(user_id=sample_user.id, content="A")
        b2 = briefing_service.create_briefing(user_id=sample_user.id, content="B")
        b3 = briefing_service.create_briefing(user_id=sample_user.id, content="C")
        all_briefings = briefing_service.get_all_briefings()
        ids = {b['id'] for b in all_briefings}
        assert b1['id'] in ids and b2['id'] in ids and b3['id'] in ids

    def test_get_user_briefings(self, briefing_service, sample_user):
        """특정 유저의 브리핑 목록 조회 테스트"""
        briefing_service.create_briefing(user_id=sample_user.id, content="1")
        briefing_service.create_briefing(user_id=sample_user.id, content="2")
        briefing_service.create_briefing(user_id=sample_user.id, content="3")
        user_briefings = briefing_service.get_user_briefings(sample_user.id)
        assert len(user_briefings) == 3
        assert all(b['user_id'] == str(sample_user.id) for b in user_briefings)

    def test_update_briefing(self, briefing_service, sample_user):
        """브리핑 업데이트 테스트"""
        created = briefing_service.create_briefing(user_id=sample_user.id, content="업데이트 전")
        updated = briefing_service.update_briefing(uuid.UUID(created['id']), content="업데이트 후")
        assert updated['id'] == created['id']
        assert updated['content'] == "업데이트 후"

    def test_update_briefing_not_found(self, briefing_service):
        """존재하지 않는 브리핑 업데이트 시도 테스트"""
        with pytest.raises(ValueError):
            briefing_service.update_briefing(uuid.uuid4(), content="없는 브리핑")

    def test_delete_briefing(self, briefing_service, sample_user):
        """브리핑 삭제 테스트"""
        created = briefing_service.create_briefing(user_id=sample_user.id, content="삭제 테스트")
        result = briefing_service.delete_briefing(uuid.UUID(created['id']))
        assert result is True
        with pytest.raises(ValueError):
            briefing_service.get_briefing(uuid.UUID(created['id']))

    def test_delete_briefing_not_found(self, briefing_service):
        """존재하지 않는 브리핑 삭제 시도 테스트"""
        result = briefing_service.delete_briefing(uuid.uuid4())
        assert result is False

    def test_get_user_briefings_empty(self, briefing_service, sample_user):
        """브리핑이 없는 사용자의 브리핑 조회 테스트"""
        # 모든 브리핑 삭제
        for b in briefing_service.get_user_briefings(sample_user.id):
            briefing_service.delete_briefing(uuid.UUID(b['id']))
        user_briefings = briefing_service.get_user_briefings(sample_user.id)
        assert len(user_briefings) == 0

    def test_create_briefing_nonexistent_user(self, briefing_service):
        """존재하지 않는 사용자로 브리핑 생성 시도 테스트"""
        with pytest.raises(Exception):
            briefing_service.create_briefing(user_id=uuid.uuid4(), content="없는 유저") 