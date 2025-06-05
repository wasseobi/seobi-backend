import uuid
from datetime import datetime, timedelta
import pytest
from app.dao.report_dao import ReportDAO
from app.dao.user_dao import UserDAO
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
            created_at=datetime.utcnow()
        )
        db.session.refresh(report)
        return report

def test_get_by_id(report_dao, sample_report):
    result = report_dao.get_by_id(sample_report.id)
    assert result is not None
    assert result.id == sample_report.id
    assert result.title == "Test Report"

def test_get_all(report_dao, sample_report, sample_user):
    """get_all() 메서드 테스트"""
    # Given
    # 추가 리포트 생성
    new_report = report_dao.create(
        user_id=sample_user.id,
        title="Another Report",
        content={"summary": "Another content"},
        type="weekly",
        created_at=datetime.utcnow() + timedelta(days=1)
    )

    # When
    results = report_dao.get_all()

    # Then
    assert len(results) == 2
    # created_at desc 순서 확인
    assert results[0].id == new_report.id  # 더 최신 리포트
    assert results[1].id == sample_report.id

def test_get_by_user(report_dao, sample_report):
    results = report_dao.get_by_user(sample_report.user_id)
    assert len(results) == 1
    assert results[0].id == sample_report.id

def test_get_by_user_and_type(report_dao, sample_report):
    results = report_dao.get_by_user_and_type(sample_report.user_id, "daily")
    assert len(results) == 1
    assert results[0].id == sample_report.id

    # 다른 타입으로 조회 시 빈 리스트 반환
    results = report_dao.get_by_user_and_type(sample_report.user_id, "weekly")
    assert len(results) == 0

def test_get_all_by_user_id_in_range(report_dao, sample_report):
    start = datetime.utcnow() - timedelta(days=1)
    end = datetime.utcnow() + timedelta(days=1)
    
    results = report_dao.get_all_by_user_id_in_range(sample_report.user_id, start, end)
    assert len(results) == 1
    assert results[0].id == sample_report.id

    # 범위 밖의 날짜로 조회
    past_start = datetime.utcnow() - timedelta(days=3)
    past_end = datetime.utcnow() - timedelta(days=2)
    results = report_dao.get_all_by_user_id_in_range(sample_report.user_id, past_start, past_end)
    assert len(results) == 0

def test_get_reports_by_month(report_dao, sample_report):
    now = datetime.utcnow()
    results = report_dao.get_reports_by_month(sample_report.user_id, now.year, now.month)
    assert len(results) == 1
    assert results[0].id == sample_report.id

    # 다른 달로 조회
    results = report_dao.get_reports_by_month(sample_report.user_id, now.year, (now.month + 1) % 12 or 12)
    assert len(results) == 0

def test_create(report_dao, sample_user):
    """create() 메서드 테스트"""
    # Given
    data = {
        "user_id": sample_user.id,
        "title": "New Report",
        "content": {"summary": "New content"},
        "type": "weekly",
        "created_at": datetime.utcnow()
    }
    
    # When
    report = report_dao.create(**data)

    # Then
    assert report is not None
    assert report.title == "New Report"
    assert report.type == "weekly"

    # DB에서 확인
    saved_report = report_dao.get_by_id(report.id)
    assert saved_report is not None
    assert saved_report.title == "New Report"

def test_delete(report_dao, sample_report):
    # 삭제 성공
    assert report_dao.delete(sample_report.id) is True
    assert Report.query.get(sample_report.id) is None

    # 존재하지 않는 ID로 삭제 시도
    assert report_dao.delete(uuid.uuid4()) is False
