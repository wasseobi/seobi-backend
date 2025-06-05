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
            title="Test Report",
            content={"summary": "Test content"},
            type="daily",
            created_at=datetime.now(timezone.utc)
        )
        db.session.refresh(report)
        return report

@pytest.mark.run(order=3)  # DB 설정(1) -> 모델(2) -> DAO(3) -> Service(4) -> Route(5) -> DB 정리(6)
class TestReportDAO:
    """ReportDAO 테스트 클래스"""

    def test_get_by_id(self, app, report_dao, sample_report):
        """get_by_id() 메서드 테스트"""
        with app.app_context():
            # When
            found_report = report_dao.get_by_id(sample_report.id)

            # Then
            assert found_report is not None
            assert found_report.id == sample_report.id
            assert found_report.title == sample_report.title
            assert found_report.content == sample_report.content

    def test_get_nonexistent_by_id(self, app, report_dao):
        """존재하지 않는 ID로 get_by_id() 메서드 테스트"""
        with app.app_context():
            # When
            report = report_dao.get_by_id(uuid.uuid4())

            # Then
            assert report is None

    def test_get_all(self, app, report_dao, sample_user):
        """get_all() 메서드 테스트"""
        with app.app_context():
            # Given
            now = datetime.now(timezone.utc)
            # 첫 번째 리포트
            report1 = report_dao.create(
                user_id=sample_user.id,
                title="Report 1",
                content={"summary": "Content 1"},
                type="daily",
                created_at=now
            )
            # 두 번째 리포트
            report2 = report_dao.create(
                user_id=sample_user.id,
                title="Report 2",
                content={"summary": "Content 2"},
                type="weekly",
                created_at=now + timedelta(hours=1)
            )

            # When
            reports = report_dao.get_all()

            # Then
            assert len(reports) >= 2
            # created_at 기준 오름차순 정렬 확인
            assert reports[0].created_at <= reports[1].created_at
            report_ids = {r.id for r in reports}
            assert report1.id in report_ids
            assert report2.id in report_ids

    def test_get_by_user(self, app, report_dao, sample_report):
        """get_by_user() 메서드 테스트"""
        with app.app_context():
            # When
            reports = report_dao.get_by_user(sample_report.user_id)

            # Then
            assert len(reports) >= 1
            assert reports[0].id == sample_report.id
            assert reports[0].user_id == sample_report.user_id

    def test_get_by_user_and_type(self, app, report_dao, sample_report):
        """get_by_user_and_type() 메서드 테스트"""
        with app.app_context():
            # When
            reports = report_dao.get_by_user_and_type(sample_report.user_id, "daily")

            # Then
            assert len(reports) >= 1
            assert reports[0].id == sample_report.id
            assert reports[0].type == "daily"

            # 다른 타입으로 조회 시 빈 리스트 반환
            other_reports = report_dao.get_by_user_and_type(sample_report.user_id, "weekly")
            assert len(other_reports) == 0

    def test_get_all_by_user_id_in_range(self, app, report_dao, sample_user):
        """get_all_by_user_id_in_range() 메서드 테스트"""
        with app.app_context():
            # Given
            now = datetime.now(timezone.utc)
            # 범위 내 리포트
            report = report_dao.create(
                user_id=sample_user.id,
                title="Test Report",
                content={"summary": "Test content"},
                type="daily",
                created_at=now
            )

            # When
            start_time = now - timedelta(hours=1)
            end_time = now + timedelta(hours=1)
            reports = report_dao.get_all_by_user_id_in_range(sample_user.id, start_time, end_time)

            # Then
            assert len(reports) >= 1
            assert reports[0].id == report.id
            
            # 범위 밖 조회
            past_start = now - timedelta(days=2)
            past_end = now - timedelta(days=1)
            past_reports = report_dao.get_all_by_user_id_in_range(sample_user.id, past_start, past_end)
            assert len(past_reports) == 0

    def test_get_reports_by_month(self, app, report_dao, sample_user):
        """get_reports_by_month() 메서드 테스트"""
        with app.app_context():
            # Given
            now = datetime.now(timezone.utc)
            report = report_dao.create(
                user_id=sample_user.id,
                title="Monthly Report",
                content={"summary": "Monthly content"},
                type="daily",
                created_at=now
            )

            # When
            reports = report_dao.get_reports_by_month(sample_user.id, now.year, now.month)

            # Then
            assert len(reports) >= 1
            assert reports[0].id == report.id

            # 다른 달 조회
            next_month = (now.month % 12) + 1
            next_year = now.year + (1 if next_month == 1 else 0)
            other_reports = report_dao.get_reports_by_month(sample_user.id, next_year, next_month)
            assert len(other_reports) == 0

    def test_create(self, app, report_dao, sample_user):
        """create() 메서드 테스트"""
        with app.app_context():
            # Given
            now = datetime.now(timezone.utc)
            data = {
                "user_id": sample_user.id,
                "title": "New Report",
                "content": {"summary": "New content"},
                "type": "weekly",
                "created_at": now
            }

            # When
            report = report_dao.create(**data)

            # Then
            assert report is not None
            assert report.id is not None
            assert report.user_id == sample_user.id
            assert report.title == data["title"]
            assert report.content == data["content"]
            assert report.type == data["type"]
            assert isinstance(report.id, uuid.UUID)
            assert isinstance(report.created_at, datetime)

    def test_delete(self, app, report_dao, sample_report):
        """delete() 메서드 테스트"""
        with app.app_context():
            # When
            result = report_dao.delete(sample_report.id)

            # Then
            assert result is True
            deleted_report = report_dao.get_by_id(sample_report.id)
            assert deleted_report is None

            # 존재하지 않는 ID로 삭제 시도
            assert report_dao.delete(uuid.uuid4()) is False
