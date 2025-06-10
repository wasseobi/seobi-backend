from app.models.db import db
import uuid
from sqlalchemy.dialects.postgresql import UUID, ENUM, JSONB
from datetime import datetime, timezone

class AutoTask(db.Model):
    __tablename__ = 'auto_task'
    id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = db.Column(UUID(as_uuid=True), db.ForeignKey('user.id'), nullable=False)
    title = db.Column(db.Text, nullable=False) # 업무 제목
    description = db.Column(db.Text, nullable=True) # 업무 설명 (상세 설명)
    repeat = db.Column(db.Text, nullable=True)  # cron 등 반복 조건 (스케줄러용)
    created_at = db.Column(db.DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
    start_at = db.Column(db.DateTime(timezone=True), nullable=True)
    finish_at = db.Column(db.DateTime(timezone=True), nullable=True)
    preferred_at = db.Column(db.DateTime(timezone=True), nullable=True)  # 유저 선호 실행시각 (예: "매일 7시" 등)
    active = db.Column(db.Boolean, default=True, nullable=False)    # 활성화/비활성화(ON/OFF) 상태
    task_list = db.Column(db.JSON, nullable=True) # 종속성 업무
    tool = db.Column(JSONB, nullable=True)
    linked_service = db.Column(JSONB, nullable=True)
    current_step = db.Column(JSONB, nullable=True)    # 현재 실행 중인 step_id(진행중 관리)
    status = db.Column(ENUM('undone', 'doing', 'done', 'failed', 'cancelled', name='auto_task_status'), nullable=False, default='undone')
    output = db.Column(db.JSON, nullable=True)
    meta = db.Column(db.JSON, nullable=True)    # 확장 필드(상태/세부 설정 등 자유 확장)

    # 관계 설정
    auto_task_steps = db.relationship('AutoTaskStep', back_populates='auto_task', cascade='all, delete-orphan', lazy="select")
    user = db.relationship('User', back_populates='auto_tasks')