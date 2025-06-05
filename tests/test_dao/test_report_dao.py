import uuid
from datetime import datetime, timedelta, timezone
import pytest
from app.dao.report_dao import ReportDAO
from app.dao.user_dao import UserDAO
from app.dao.session_dao import SessionDAO
from app.models.session import Session
from app.models.user import User
from app.models import Report, db

@pytest.fixture(autouse=True)
def setup_teardown(app):
    """각 테스트 전후로 데이터베이스를 정리하는 fixture"""
    with app.app_context():
        yield
        db.session.rollback()
        Report.query.delete()
        Session.query.delete()
        User.query.delete()
        db.session.commit()

@pytest.fixture
def report_dao(app):
    with app.app_context():
        return ReportDAO()

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
def sample_report(app, report_dao, sample_user):
    """테스트용 리포트를 생성하는 fixture"""
    with app.app_context():
        report = report_dao.create(
            user_id=sample_user.id,
            content={"text": "Test content"},
            type="daily",
            created_at=datetime.now(timezone.utc)
        )
        db.session.refresh(report)
        return report

@pytest.mark.run(order=3)  # DB 설정(1) -> 모델(2) -> DAO(3) -> Service(4) -> Route(5) -> DB 정리(6)
class TestReportDAO:
    """ReportDAO 테스트 클래스"""

    def test_get_by_id(self, report_dao, sample_report):
        """get_all() 메서드로 ID로 리포트 조회 테스트"""
        found_report = report_dao.get_all(sample_report.id)
        assert found_report is not None
        assert found_report.id == sample_report.id
        assert found_report.content == sample_report.content

    def test_get_nonexistent_by_id(self, report_dao):
        """존재하지 않는 리포트 조회 테스트"""
        found_report = report_dao.get_all(uuid.uuid4())
        assert found_report is None

    def test_get_by_user(self, report_dao, sample_user):
        """get_by_user() 메서드 테스트"""
        # Given
        report1 = report_dao.create(
            user_id=sample_user.id,
            content={"text": "Content 2"},
            type="daily"
        )
        report2 = report_dao.create(
            user_id=sample_user.id,
            content={"text": "Content 2"},
            type="weekly"
        )

        # When
        reports = report_dao.get_by_user(sample_user.id)

        # Then
        assert len(reports) == 2
        report_ids = {r.id for r in reports}
        assert report1.id in report_ids
        assert report2.id in report_ids

    def test_get_by_user_and_type(self, report_dao, sample_user):
        """get_by_user_and_type() 메서드 테스트"""
        # Given
        report1 = report_dao.create(
            user_id=sample_user.id,
            content={"sections": "Content 2"},
            type="daily"
        )
        report2 = report_dao.create(
            user_id=sample_user.id,
            content={"sections": "Content 2"},
            type="weekly"
        )

        # When
        daily_reports = report_dao.get_by_user_and_type(sample_user.id, "daily")

        # Then
        assert len(daily_reports) == 1
        assert daily_reports[0].id == report1.id
        assert daily_reports[0].type == "daily"

    def test_get_all_by_user_id_in_range(self, report_dao, sample_user):
        """get_all_by_user_id_in_range() 메서드 테스트"""
        # Given
        now = datetime.now(timezone.utc)
        report1 = report_dao.create(
            user_id=sample_user.id,
            content={"sections": "Content 2"},
            type="daily"
        )
        report2 = report_dao.create(
            user_id=sample_user.id,
            content={"sections": "Content 2"},
            type="weekly"
        )

        # When
        start_date = now - timedelta(days=1)
        end_date = now + timedelta(days=1)
        reports = report_dao.get_all_by_user_id_in_range(sample_user.id, start_date, end_date)

        # Then
        assert len(reports) == 2
        report_ids = {r.id for r in reports}
        assert report1.id in report_ids
        assert report2.id in report_ids

    def test_get_reports_by_month(self, report_dao, sample_user):
        """get_reports_by_month() 메서드 테스트"""
        # Given
        now = datetime.now(timezone.utc)
        report = report_dao.create(
            user_id=sample_user.id,
            content={"sections": "Content 2"},
            type="monthly"
        )

        # When
        reports = report_dao.get_reports_by_month(sample_user.id, now.year, now.month)

        # Then
        assert len(reports) > 0
        assert report.id in {r.id for r in reports}

    def test_create(self, report_dao, sample_user):
        """create() 메서드 테스트"""
        # Given
        content = {"sections": "Content 2"}
        report_type = "daily"

        # When
        report = report_dao.create(
            user_id=sample_user.id,
            content=content,
            type=report_type
        )

        # Then
        assert report is not None
        assert isinstance(report.id, uuid.UUID)
        assert report.user_id == sample_user.id
        assert report.content == content
        assert report.type == report_type
        assert report.created_at is not None

    def test_get_all(self, report_dao, sample_user):
        """get_all() 메서드 테스트"""
        # Given
        report1 = report_dao.create(
            user_id=sample_user.id,
            content={"sections": "Content 2"},
            type="daily"
        )
        report2 = report_dao.create(
            user_id=sample_user.id,
            content={"sections": "Content 2"},
            type="weekly"
        )

        # When
        all_reports = report_dao.get_all(report1.id)

        # Then
        assert all_reports is not None
        assert all_reports.id == report1.id

    def test_delete(self, report_dao, sample_report):
        """delete() 메서드 테스트"""
        # When
        result = report_dao.delete(sample_report.id)

        # Then
        assert result is True
        deleted_report = report_dao.get_all(sample_report.id)
        assert deleted_report is None
