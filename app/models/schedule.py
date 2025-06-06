from app.models.db import db
import uuid
from sqlalchemy.dialects.postgresql import UUID, ENUM
from datetime import datetime, timezone

class Schedule(db.Model):
    __tablename__ = 'schedule'
    id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = db.Column(UUID(as_uuid=True), db.ForeignKey('user.id'), nullable=False)
    title = db.Column(db.Text, nullable=False)
    repeat = db.Column(db.Text, nullable=True)  # cron 표현식 등 반복 일정 관리
    start_at = db.Column(db.DateTime(timezone=True), nullable=True)  # 시작 시간
    finish_at = db.Column(db.DateTime(timezone=True), nullable=True)  # 종료 시간
    location = db.Column(db.Text, nullable=True) # 우선은 Text로 저장. but 추후 바꿀 수 있음. 좌표값이라던지.
    status = db.Column(ENUM('undone', 'done', name='schedule_status_enum'), nullable=False, default='undone')
    memo = db.Column(db.Text, nullable=True)
    linked_service = db.Column(db.Text, nullable=False)  # 외부 연동 서비스명 등
    created_at = db.Column(db.DateTime(
        timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)

    # 관계 설정 (User와 연결)
    user = db.relationship('User', back_populates='schedules')
