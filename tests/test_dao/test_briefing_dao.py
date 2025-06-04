import pytest
import uuid
from app.dao.briefing_dao import BriefingDAO
from app.dao.user_dao import UserDAO
from app.models.briefing import Briefing
from app.models.user import User
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
def briefing_dao(app):
    with app.app_context():
        return BriefingDAO()

@pytest.fixture
def user_dao(app):
    with app.app_context():
        return UserDAO()

@pytest.fixture
def sample_user(user_dao):
    return user_dao.create(username="testuser", email="test@example.com")

@pytest.fixture
def sample_briefing(briefing_dao, sample_user):
    return briefing_dao.create(user_id=sample_user.id, content="테스트 브리핑")

@pytest.mark.run(order=3)
class TestBriefingDAO:
    """BriefingDAO 테스트 클래스"""
    def test_get_nonexistent_by_id(self, briefing_dao):
        """존재하지 않는 ID로 get_by_id() 테스트"""
        briefing = briefing_dao.get_by_id(uuid.uuid4())
        assert briefing is None

    def test_get_all_briefings(self, briefing_dao, sample_user):
        """get_all() 메서드 테스트"""
        b1 = briefing_dao.create(user_id=sample_user.id, content="A")
        b2 = briefing_dao.create(user_id=sample_user.id, content="B")
        b3 = briefing_dao.create(user_id=sample_user.id, content="C")
        briefings = briefing_dao.get_all()
        assert len(briefings) >= 3
        ids = {b.id for b in briefings}
        assert b1.id in ids and b2.id in ids and b3.id in ids

    def test_delete_briefing(self, briefing_dao, sample_briefing):
        """delete() 메서드 테스트"""
        result = briefing_dao.delete(sample_briefing.id)
        assert result is True
        assert briefing_dao.get_by_id(sample_briefing.id) is None

    def test_delete_nonexistent_briefing(self, briefing_dao):
        """존재하지 않는 ID로 delete() 테스트"""
        result = briefing_dao.delete(uuid.uuid4())
        assert result is False

    def test_create_briefing(self, briefing_dao, sample_user):
        """create() 메서드 테스트"""
        briefing = briefing_dao.create(user_id=sample_user.id, content="새 브리핑")
        assert briefing is not None
        assert briefing.id is not None
        assert briefing.user_id == sample_user.id
        assert briefing.content == "새 브리핑"

    def test_get_all_by_user_id(self, briefing_dao, sample_user):
        """get_all_by_user_id() 메서드 테스트"""
        briefing_dao.create(user_id=sample_user.id, content="1")
        briefing_dao.create(user_id=sample_user.id, content="2")
        briefing_dao.create(user_id=sample_user.id, content="3")
        briefings = briefing_dao.get_all_by_user_id(sample_user.id)
        assert len(briefings) == 3
        assert all(b.user_id == sample_user.id for b in briefings)
        # 최신순 정렬 확인
        assert briefings[0].created_at >= briefings[1].created_at >= briefings[2].created_at

    def test_get_user_briefings_empty(self, briefing_dao, sample_user):
        """브리핑이 없는 사용자의 브리핑 조회 테스트"""
        Briefing.query.filter_by(user_id=sample_user.id).delete()
        db.session.commit()
        briefings = briefing_dao.get_all_by_user_id(sample_user.id)
        assert len(briefings) == 0

    def test_get_nonexistent_user_briefings(self, briefing_dao):
        """존재하지 않는 사용자의 브리핑 조회 테스트"""
        briefings = briefing_dao.get_all_by_user_id(uuid.uuid4())
        assert len(briefings) == 0

    def test_create_briefing_nonexistent_user(self, briefing_dao):
        """존재하지 않는 사용자로 브리핑 생성 시도 테스트"""
        with pytest.raises(Exception):
            briefing_dao.create(user_id=uuid.uuid4(), content="없는 유저")

    def test_update_briefing(self, briefing_dao, sample_briefing):
        """update() 메서드 테스트"""
        updated = briefing_dao.update(sample_briefing.id, content="수정된 내용")
        assert updated is not None
        assert updated.content == "수정된 내용"

    def test_update_briefing_partial(self, briefing_dao, sample_briefing):
        """일부 필드만 업데이트 테스트"""
        original_content = sample_briefing.content
        updated = briefing_dao.update(sample_briefing.id)
        assert updated is not None
        assert updated.content == original_content 