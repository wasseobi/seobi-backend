import uuid
from datetime import datetime, timedelta
import pytest
from app.dao.report_dao import ReportDAO
from app.models import Report, db

@pytest.fixture
def report_dao():
    return ReportDAO()

@pytest.fixture
def sample_report(db_session):
    user_id = uuid.uuid4()
    report = Report(
        user_id=user_id,
        title="Test Report",
        content={"summary": "Test content"},
        type="daily",
        created_at=datetime.utcnow()
    )
    db_session.add(report)
    db_session.commit()
    return report

def test_get_by_id(report_dao, sample_report):
    result = report_dao.get_by_id(sample_report.id)
    assert result is not None
    assert result.id == sample_report.id
    assert result.title == "Test Report"

def test_get_all(report_dao, sample_report):
    # 추가 리포트 생성
    user_id = uuid.uuid4()
    new_report = Report(
        user_id=user_id,
        title="Another Report",
        content={"summary": "Another content"},
        type="weekly",
        created_at=datetime.utcnow() + timedelta(days=1)
    )
    db.session.add(new_report)
    db.session.commit()

    # 전체 리포트 조회
    results = report_dao.get_all()
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

def test_create(report_dao, db_session):
    user_id = uuid.uuid4()
    data = {
        "user_id": user_id,
        "title": "New Report",
        "content": {"summary": "New content"},
        "type": "weekly",
        "created_at": datetime.utcnow()
    }
    
    report = report_dao.create(**data)
    assert report is not None
    assert report.title == "New Report"
    assert report.type == "weekly"

    # DB에서 확인
    saved_report = Report.query.get(report.id)
    assert saved_report is not None
    assert saved_report.title == "New Report"

def test_delete(report_dao, sample_report):
    # 삭제 성공
    assert report_dao.delete(sample_report.id) is True
    assert Report.query.get(sample_report.id) is None

    # 존재하지 않는 ID로 삭제 시도
    assert report_dao.delete(uuid.uuid4()) is False
