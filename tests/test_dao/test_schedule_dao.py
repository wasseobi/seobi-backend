import pytest
from datetime import datetime, timedelta, timezone
from app.dao.schedule_dao import ScheduleDAO
from app.models import Schedule, User
from app.models.db import db
import uuid

@pytest.fixture(autouse=True)
def setup_teardown(app):
    """각 테스트 전후로 데이터베이스를 정리하는 fixture"""
    with app.app_context():
        yield
        db.session.rollback()
        # Schedule과 User 테이블 모두 정리
        Schedule.query.delete()
        User.query.delete()
        db.session.commit()

@pytest.fixture
def schedule_dao(app):
    """ScheduleDAO 인스턴스를 생성하는 fixture"""
    with app.app_context():
        return ScheduleDAO()

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
def sample_schedule(app, schedule_dao, sample_user):
    """테스트용 스케줄을 생성하는 fixture"""
    with app.app_context():
        schedule = schedule_dao.create(
            user_id=sample_user.id,
            title="Test Schedule",
            memo="Test Memo",
            start_at=datetime.now(),
            finish_at=datetime.now() + timedelta(hours=1),
            status="undone",
            linked_service="test_service"  # 필수 필드
        )
        db.session.refresh(schedule)
        return schedule

@pytest.mark.run(order=3)  # DB 설정(1) -> 모델(2) -> DAO(3) -> Service(4) -> Route(5) -> DB 정리(6)
class TestScheduleDAO:
    """ScheduleDAO 테스트 클래스"""

    # BaseDAO에서 상속받은 메서드 테스트
    def test_get_by_id(self, schedule_dao, sample_schedule):
        """get() 메서드 테스트"""
        # When
        found_schedule = schedule_dao.get(sample_schedule.id)

        # Then
        assert found_schedule is not None
        assert found_schedule.id == sample_schedule.id
        assert found_schedule.title == sample_schedule.title
        assert found_schedule.memo == sample_schedule.memo

    def test_get_nonexistent_by_id(self, schedule_dao):
        """존재하지 않는 ID로 get() 메서드 테스트"""
        # When
        schedule = schedule_dao.get(uuid.uuid4())

        # Then
        assert schedule is None

    def test_get_all_schedules(self, schedule_dao, sample_user):
        """get_all() 메서드 테스트"""
        # Given
        now = datetime.now()
        schedule1 = schedule_dao.create(
            user_id=sample_user.id,
            title="Schedule 1",
            memo="Memo 1",
            start_at=now,
            finish_at=now + timedelta(hours=1),
            status="undone",
            linked_service="test_service"
        )
        schedule2 = schedule_dao.create(
            user_id=sample_user.id,
            title="Schedule 2",
            memo="Memo 2",
            start_at=now + timedelta(hours=2),
            finish_at=now + timedelta(hours=3),
            status="undone",
            linked_service="test_service"
        )

        # When
        schedules = schedule_dao.get_all()

        # Then
        assert len(schedules) >= 2
        schedule_ids = {s.id for s in schedules}
        assert schedule1.id in schedule_ids
        assert schedule2.id in schedule_ids
        # created_at 기준 오름차순 정렬 확인
        timestamps = [s.created_at for s in schedules]
        assert timestamps == sorted(timestamps)

    def test_get_all_by_user_id(self, schedule_dao, sample_user, other_user):
        """get_all_by_user_id() 메서드 테스트"""
        # Given
        now = datetime.now()
        schedule1 = schedule_dao.create(
            user_id=sample_user.id,
            title="Schedule 1",
            memo="Memo 1",
            start_at=now,
            finish_at=now + timedelta(hours=1),
            status="undone",
            linked_service="test_service"
        )
        schedule2 = schedule_dao.create(
            user_id=sample_user.id,
            title="Schedule 2",
            memo="Memo 2",
            start_at=now + timedelta(hours=2),
            finish_at=now + timedelta(hours=3),
            status="undone",
            linked_service="test_service"
        )
        schedule3 = schedule_dao.create(
            user_id=other_user.id,
            title="Other User Schedule",
            memo="Other Memo",
            start_at=now,
            finish_at=now + timedelta(hours=1),
            status="undone",
            linked_service="test_service"
        )

        # When
        user_schedules = schedule_dao.get_all_by_user_id(sample_user.id)

        # Then
        assert len(user_schedules) == 2
        schedule_ids = {s.id for s in user_schedules}
        assert schedule1.id in schedule_ids
        assert schedule2.id in schedule_ids
        assert schedule3.id not in schedule_ids
        # timestamp 기준 오름차순 정렬 확인
        timestamps = [s.created_at for s in user_schedules]
        assert timestamps == sorted(timestamps)

    def test_get_all_by_user_id_in_range(self, schedule_dao, sample_user):
        """get_all_by_user_id_in_range_status() 메서드 테스트"""
        # Given
        now = datetime.now()
        base_time = datetime(now.year, now.month, now.day, 10, 0)  # 오늘 10:00
        
        # 범위 내 스케줄
        in_range_schedule = schedule_dao.create(
            user_id=sample_user.id,
            title="In Range Schedule",
            memo="Memo 1",
            start_at=base_time + timedelta(hours=1),
            finish_at=base_time + timedelta(hours=2),
            status="undone",
            linked_service="test_service"
        )
        
        # 범위 밖 스케줄
        out_of_range_schedule = schedule_dao.create(
            user_id=sample_user.id,
            title="Out of Range Schedule",
            memo="Memo 2",
            start_at=base_time + timedelta(hours=4),
            finish_at=base_time + timedelta(hours=5),
            status="undone",
            linked_service="test_service"
        )

        # When
        start_time = base_time
        end_time = base_time + timedelta(hours=3)
        schedules = schedule_dao.get_all_by_user_id_in_range_status(
            sample_user.id,
            start_time,
            end_time
        )

        # Then
        assert len(schedules) == 1
        assert schedules[0].id == in_range_schedule.id
        assert schedules[0].id != out_of_range_schedule.id

    def test_get_all_by_user_id_in_range_with_status(self, schedule_dao, sample_user):
        """get_all_by_user_id_in_range_status() 메서드의 status 필터링 테스트"""
        # Given
        now = datetime.now()
        base_time = datetime(now.year, now.month, now.day, 10, 0)  # 오늘 10:00
        
        # 같은 시간대에 다른 상태의 스케줄
        undone_schedule = schedule_dao.create(
            user_id=sample_user.id,
            title="Undone Schedule",
            memo="Memo 1",
            start_at=base_time + timedelta(hours=1),
            finish_at=base_time + timedelta(hours=2),
            status="undone",
            linked_service="test_service"
        )
        done_schedule = schedule_dao.create(
            user_id=sample_user.id,
            title="Done Schedule",
            memo="Memo 2",
            start_at=base_time + timedelta(hours=1),
            finish_at=base_time + timedelta(hours=2),
            status="done",
            linked_service="test_service"
        )

        # When
        start_time = base_time
        end_time = base_time + timedelta(hours=3)
        undone_schedules = schedule_dao.get_all_by_user_id_in_range_status(
            sample_user.id,
            start_time,
            end_time,
            status="undone"
        )
        done_schedules = schedule_dao.get_all_by_user_id_in_range_status(
            sample_user.id,
            start_time,
            end_time,
            status="done"
        )

        # Then
        assert len(undone_schedules) == 1
        assert len(done_schedules) == 1
        assert undone_schedules[0].id == undone_schedule.id
        assert done_schedules[0].id == done_schedule.id

    def test_create_schedule(self, schedule_dao, sample_user):
        """스케줄 생성 테스트"""
        # Given
        now = datetime.now(timezone.utc)  # UTC timezone 추가
        title = "New Schedule"
        memo = "New Memo"
        start_at = now
        finish_at = now + timedelta(hours=1)
        status = "undone"
        linked_service = "test_service"

        # When
        schedule = schedule_dao.create(
            user_id=sample_user.id,
            title=title,
            memo=memo,
            start_at=start_at,
            finish_at=finish_at,
            status=status,
            linked_service=linked_service
        )

        # Then
        assert schedule is not None
        assert schedule.id is not None
        assert schedule.user_id == sample_user.id
        assert schedule.title == title
        assert schedule.memo == memo
        assert schedule.start_at == start_at
        assert schedule.finish_at == finish_at
        assert schedule.status == status
        assert schedule.linked_service == linked_service
        assert isinstance(schedule.id, uuid.UUID)

    def test_update_schedule(self, schedule_dao, sample_schedule):
        """스케줄 업데이트 테스트"""
        # Given
        new_title = "Updated Schedule"
        new_memo = "Updated Memo"
        new_status = "done"

        # When
        updated_schedule = schedule_dao.update(
            sample_schedule.id,
            title=new_title,
            memo=new_memo,
            status=new_status
        )

        # Then
        assert updated_schedule is not None
        assert updated_schedule.id == sample_schedule.id
        assert updated_schedule.title == new_title
        assert updated_schedule.memo == new_memo
        assert updated_schedule.status == new_status
        assert updated_schedule.user_id == sample_schedule.user_id  # user_id는 변경되지 않아야 함
        assert updated_schedule.start_at == sample_schedule.start_at  # start_at은 변경되지 않아야 함
        assert updated_schedule.finish_at == sample_schedule.finish_at  # finish_at은 변경되지 않아야 함
        assert updated_schedule.linked_service == sample_schedule.linked_service  # linked_service는 변경되지 않아야 함

    def test_update_schedule_partial(self, schedule_dao, sample_schedule):
        """스케줄 부분 업데이트 테스트"""
        # Given
        original_title = sample_schedule.title
        new_status = "done"

        # When
        updated_schedule = schedule_dao.update(
            sample_schedule.id,
            status=new_status
        )

        # Then
        assert updated_schedule is not None
        assert updated_schedule.id == sample_schedule.id
        assert updated_schedule.title == original_title  # title은 변경되지 않아야 함
        assert updated_schedule.status == new_status
        assert updated_schedule.user_id == sample_schedule.user_id
        assert updated_schedule.start_at == sample_schedule.start_at
        assert updated_schedule.finish_at == sample_schedule.finish_at
        assert updated_schedule.linked_service == sample_schedule.linked_service

    def test_get_all(self, schedule_dao, sample_user, other_user):
        """get_all() 메서드 테스트"""
        # Given
        now = datetime.now(timezone.utc)
        # 첫 번째 사용자의 일정
        schedule1 = schedule_dao.create(
            user_id=sample_user.id,
            title="Test Schedule 1",
            created_at=now,
            start_at=now,
            linked_service="test_service"
        )
        # 두 번째 사용자의 일정
        schedule2 = schedule_dao.create(
            user_id=other_user.id,
            title="Test Schedule 2",
            created_at=now + timedelta(hours=1),
            start_at=now + timedelta(hours=1),
            linked_service="test_service"
        )

        # When
        schedules = schedule_dao.get_all()

        # Then
        assert len(schedules) == 2
        # timestamp 기준 오름차순 정렬 확인
        assert schedules[0].id == schedule1.id
        assert schedules[1].id == schedule2.id

    def test_get_count_by_date_range(self, schedule_dao, sample_user):
        """get_count_by_date_range() 메서드 테스트"""
        # Given
        now = datetime.now(timezone.utc)
        yesterday = now - timedelta(days=1)
        tomorrow = now + timedelta(days=1)

        # 어제 일정
        schedule_dao.create(
            user_id=sample_user.id,
            title="Yesterday Schedule",
            created_at=yesterday,
            start_at=yesterday,
            status="done",
            linked_service="test_service"
        )

        # 오늘 일정
        schedule_dao.create(
            user_id=sample_user.id,
            title="Today Schedule 1",
            created_at=now,
            start_at=now,
            status="undone",
            linked_service="test_service"
        )
        schedule_dao.create(
            user_id=sample_user.id,
            title="Today Schedule 2",
            created_at=now,
            start_at=now,
            status="undone",
            linked_service="test_service"
        )

        # When & Then
        # 전체 기간 조회
        count = schedule_dao.get_count_by_date_range(
            sample_user.id,
            yesterday,
            tomorrow
        )
        assert count == 3

        # 상태별 조회
        done_count = schedule_dao.get_count_by_date_range(
            sample_user.id,
            yesterday,
            tomorrow,
            status="done"
        )
        assert done_count == 1

        undone_count = schedule_dao.get_count_by_date_range(
            sample_user.id,
            yesterday,
            tomorrow,
            status="undone"
        )
        assert undone_count == 2

        # 범위 밖의 날짜로 조회
        out_of_range_count = schedule_dao.get_count_by_date_range(
            sample_user.id,
            now - timedelta(days=3),
            now - timedelta(days=2)
        )
        assert out_of_range_count == 0