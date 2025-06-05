import pytest
from datetime import datetime, timedelta, timezone
from app.dao.insight_article_dao import InsightArticleDAO
from app.models import InsightArticle, User
from app.models.db import db
import uuid

@pytest.fixture(autouse=True)
def setup_teardown(app):
    """각 테스트 전후로 데이터베이스를 정리하는 fixture"""
    with app.app_context():
        yield
        db.session.rollback()
        # InsightArticle과 User 테이블 모두 정리
        InsightArticle.query.delete()
        User.query.delete()
        db.session.commit()

@pytest.fixture
def insight_article_dao(app):
    """InsightArticleDAO 인스턴스를 생성하는 fixture"""
    with app.app_context():
        return InsightArticleDAO()

@pytest.fixture
def sample_user(app):
    """테스트용 사용자를 생성하는 fixture"""
    from app.dao.user_dao import UserDAO
    with app.app_context():
        user_dao = UserDAO()
        user = user_dao.create(
            username="testuser",
            email="test@example.com"
        )
        db.session.refresh(user)
        return user

@pytest.fixture
def other_user(app):
    """테스트용 다른 사용자를 생성하는 fixture"""
    from app.dao.user_dao import UserDAO
    with app.app_context():
        user_dao = UserDAO()
        user = user_dao.create(
            username="otheruser",
            email="other@example.com"
        )
        db.session.refresh(user)
        return user

@pytest.fixture
def sample_article(app, insight_article_dao, sample_user):
    """테스트용 인사이트 아티클을 생성하는 fixture"""
    with app.app_context():
        article = insight_article_dao.create(
            user_id=sample_user.id,
            title="Test Article",
            content={"sections": ["Test Content"]},
            source="Test Source",
            type="chat",
            tags=["tag1", "tag2"],
            keywords=["keyword1", "keyword2"],
            interest_ids=[str(uuid.uuid4())],
            created_at=datetime.now(timezone.utc)
        )
        db.session.refresh(article)
        return article

@pytest.mark.run(order=3)  # DB 설정(1) -> 모델(2) -> DAO(3) -> Service(4) -> Route(5) -> DB 정리(6)
class TestInsightArticleDAO:
    """InsightArticleDAO 테스트 클래스"""

    def test_get_by_id(self, insight_article_dao, sample_article):
        """get_by_id() 메서드 테스트"""
        # When
        found_article = insight_article_dao.get_by_id(sample_article.id)

        # Then
        assert found_article is not None
        assert found_article.id == sample_article.id
        assert found_article.user_id == sample_article.user_id
        assert found_article.title == sample_article.title
        assert found_article.content == sample_article.content
        assert found_article.source == sample_article.source
        assert found_article.type == sample_article.type
        assert found_article.tags == sample_article.tags
        assert found_article.keywords == sample_article.keywords
        assert found_article.interest_ids == sample_article.interest_ids
        assert found_article.created_at == sample_article.created_at

    def test_get_nonexistent_by_id(self, insight_article_dao):
        """존재하지 않는 ID로 get_by_id() 메서드 테스트"""
        # When
        article = insight_article_dao.get_by_id(uuid.uuid4())

        # Then
        assert article is None

    def test_get_all_by_user_id(self, insight_article_dao, sample_user, other_user):
        """get_all_by_user_id() 메서드 테스트"""
        # Given
        now = datetime.now(timezone.utc)
        article1 = insight_article_dao.create(
            user_id=sample_user.id,
            title="Article 1",
            content={"sections": ["Content 1"]},
            source="Test Source 1",
            type="chat",
            tags=["tag1"],
            keywords=["keyword1"],
            interest_ids=[str(uuid.uuid4())],
            created_at=now
        )
        article2 = insight_article_dao.create(
            user_id=sample_user.id,
            title="Article 2",
            content={"sections": ["Content 2"]},
            source="Test Source 2",
            type="report",
            tags=["tag2"],
            keywords=["keyword2"],
            interest_ids=[str(uuid.uuid4())],
            created_at=now + timedelta(hours=1)
        )
        other_article = insight_article_dao.create(
            user_id=other_user.id,
            title="Other User Article",
            content={"sections": ["Other Content"]},
            source="Other Source",
            type="chat",
            tags=["other_tag"],
            keywords=["other_keyword"],
            interest_ids=[str(uuid.uuid4())],
            created_at=now
        )

        # When
        user_articles = insight_article_dao.get_all_by_user_id(sample_user.id)

        # Then
        assert len(user_articles) == 2
        article_ids = {a.id for a in user_articles}
        assert article1.id in article_ids
        assert article2.id in article_ids
        assert other_article.id not in article_ids
        # created_at 기준 내림차순 정렬 확인
        created_ats = [a.created_at for a in user_articles]
        assert created_ats == sorted(created_ats, reverse=True)

    def test_create_article(self, insight_article_dao, sample_user):
        """인사이트 아티클 생성 테스트"""
        # Given
        now = datetime.now(timezone.utc)
        title = "New Article"
        content = {"sections": ["New Content"]}
        source = "Test Source"
        type = "chat"
        tags = ["tag1", "tag2"]
        keywords = ["keyword1", "keyword2"]
        interest_ids = [str(uuid.uuid4())]

        # When
        article = insight_article_dao.create(
            user_id=sample_user.id,
            title=title,
            content=content,
            source=source,
            type=type,
            tags=tags,
            keywords=keywords,
            interest_ids=interest_ids,
            created_at=now
        )

        # Then
        assert article is not None
        assert article.id is not None
        assert article.user_id == sample_user.id
        assert article.title == title
        assert article.content == content
        assert article.source == source
        assert article.type == type
        assert article.tags == tags
        assert article.keywords == keywords
        assert article.interest_ids == interest_ids
        assert article.created_at == now
        assert isinstance(article.id, uuid.UUID)

    def test_update_article(self, insight_article_dao, sample_article):
        """인사이트 아티클 업데이트 테스트"""
        # Given
        new_title = "Updated Article"
        new_content = {"sections": ["Updated Content"]}
        new_source = "Updated Source"
        new_type = "report"
        new_tags = ["updated_tag1", "updated_tag2"]
        new_keywords = ["updated_keyword1", "updated_keyword2"]
        new_interest_ids = [str(uuid.uuid4())]

        # When
        updated_article = insight_article_dao.update(
            sample_article.id,
            title=new_title,
            content=new_content,
            source=new_source,
            type=new_type,
            tags=new_tags,
            keywords=new_keywords,
            interest_ids=new_interest_ids
        )

        # Then
        assert updated_article is not None
        assert updated_article.id == sample_article.id
        assert updated_article.title == new_title
        assert updated_article.content == new_content
        assert updated_article.source == new_source
        assert updated_article.type == new_type
        assert updated_article.tags == new_tags
        assert updated_article.keywords == new_keywords
        assert updated_article.interest_ids == new_interest_ids
        assert updated_article.user_id == sample_article.user_id
        assert updated_article.created_at == sample_article.created_at

    def test_update_article_partial(self, insight_article_dao, sample_article):
        """인사이트 아티클 부분 업데이트 테스트"""
        # Given
        original_title = sample_article.title
        new_content = {"sections": ["Updated Content"]}
        new_tags = ["updated_tag1"]

        # When
        updated_article = insight_article_dao.update(
            sample_article.id,
            content=new_content,
            tags=new_tags
        )

        # Then
        assert updated_article is not None
        assert updated_article.id == sample_article.id
        assert updated_article.title == original_title
        assert updated_article.content == new_content
        assert updated_article.tags == new_tags
        assert updated_article.source == sample_article.source
        assert updated_article.type == sample_article.type
        assert updated_article.keywords == sample_article.keywords
        assert updated_article.interest_ids == sample_article.interest_ids
        assert updated_article.user_id == sample_article.user_id
        assert updated_article.created_at == sample_article.created_at

    def test_update(self, insight_article_dao, sample_article):
        """update() 메서드 테스트"""
        # Given
        new_title = "Updated Title"
        new_content = {"sections": ["Updated Content"]}
        new_tags = ["new_tag1", "new_tag2"]

        # When
        updated_article = insight_article_dao.update(
            sample_article.id,
            title=new_title,
            content=new_content,
            tags=new_tags
        )

        # Then
        assert updated_article is not None
        assert updated_article.id == sample_article.id
        assert updated_article.title == new_title
        assert updated_article.content == new_content
        assert updated_article.tags == new_tags
        # 다른 필드들은 변경되지 않아야 함
        assert updated_article.source == sample_article.source
        assert updated_article.type == sample_article.type
        assert updated_article.keywords == sample_article.keywords
        assert updated_article.interest_ids == sample_article.interest_ids

    def test_update_nonexistent_article(self, insight_article_dao):
        """존재하지 않는 아티클 update() 메서드 테스트"""
        # When
        updated_article = insight_article_dao.update(
            uuid.uuid4(),
            title="New Title"
        )

        # Then
        assert updated_article is None

    def test_get_all(self, insight_article_dao, sample_user, other_user):
        """get_all() 메서드 테스트"""
        # Given
        now = datetime.now(timezone.utc)
        # 첫 번째 사용자의 아티클
        article1 = insight_article_dao.create(
            user_id=sample_user.id,
            title="Article 1",
            content={"sections": ["Content 1"]},
            source="Test Source 1",
            type="chat",
            created_at=now
        )
        # 두 번째 사용자의 아티클
        article2 = insight_article_dao.create(
            user_id=other_user.id,
            title="Article 2",
            content={"sections": ["Content 2"]},
            source="Test Source 2",
            type="chat",
            created_at=now + timedelta(hours=1)
        )

        # When
        articles = insight_article_dao.get_all()

        # Then
        assert len(articles) >= 2
        # created_at 기준 오름차순 정렬 확인
        assert articles[0].created_at <= articles[1].created_at
        article_ids = {a.id for a in articles}
        assert article1.id in article_ids
        assert article2.id in article_ids

    def test_delete_article(self, insight_article_dao, sample_article):
        """delete() 메서드 테스트"""
        # When
        result = insight_article_dao.delete(sample_article.id)

        # Then
        assert result is True
        deleted_article = insight_article_dao.get_by_id(sample_article.id)
        assert deleted_article is None

    def test_delete_nonexistent_article(self, insight_article_dao):
        """존재하지 않는 아티클 delete() 메서드 테스트"""
        # When
        result = insight_article_dao.delete(uuid.uuid4())

        # Then
        assert result is False