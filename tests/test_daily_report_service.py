import uuid
import pytest
from app.services.reports.daily_report_service import DailyReportService, KST

# 테스트용 user_id를 실제 존재하는 UUID로 바꿔주세요.
TEST_USER_ID = uuid.UUID('af553404-7b43-413a-9caf-06d2e2495d8c')

@pytest.fixture
def service():
    return DailyReportService()

def test_get_today_schedules_done(service):
    result = service.get_today_schedules_done(TEST_USER_ID, KST)
    print("[DONE]", result)
    assert isinstance(result, list)
    for item in result:
        assert item['status'] == 'done'
    # 정렬 확인 (timestamp 오름차순)
    timestamps = [item['start_at'] for item in result]
    assert timestamps == sorted(timestamps)


def test_get_today_schedules_undone(service):
    result = service.get_today_schedules_undone(TEST_USER_ID, KST)
    print("[UNDONE]", result)
    assert isinstance(result, list)
    for item in result:
        assert item['status'] == 'undone'
    timestamps = [item['start_at'] for item in result]
    assert timestamps == sorted(timestamps)


def test_get_today_sessions(service):
    result = service.get_today_sessions(TEST_USER_ID, KST)
    print("[SESSIONS]", result)
    assert isinstance(result, list)
    start_ats = [item['start_at'] for item in result]
    assert start_ats == sorted(start_ats, reverse=True)


def test_get_today_articles(service):
    result = service.get_today_articles(TEST_USER_ID, KST)
    print("[ARTICLES]", result)
    assert isinstance(result, list)
    created_ats = [item['created_at'] for item in result]
    assert created_ats == sorted(created_ats, reverse=True)
