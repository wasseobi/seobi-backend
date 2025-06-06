from app.models.db import db
import uuid
from sqlalchemy.dialects.postgresql import UUID, ENUM
from datetime import datetime, timezone

class AutoTask(db.Model):
    __tablename__ = 'auto_task'
    id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = db.Column(UUID(as_uuid=True), db.ForeignKey('user.id'), nullable=False)
    title = db.Column(db.Text, nullable=False) # 업무 제목
    description = db.Column(db.Text, nullable=True) # 업무 설명
    repeat = db.Column(db.Text, nullable=True)  # cron 표현식 등 반복 일정 관리
    created_at = db.Column(db.DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
    start_at = db.Column(db.DateTime(timezone=True), nullable=True)
    finish_at = db.Column(db.DateTime(timezone=True), nullable=True)
    preferred_at = db.Column(db.DateTime(timezone=True), nullable=True)
    task_list = db.Column(db.JSON, nullable=True) # 종속성이 있는 업무 목록(JSON)
    tool = db.Column(db.Text, nullable=True)
    linked_service = db.Column(db.Text, nullable=True)  # 외부 연동 서비스명 등
    steps = db.Column(db.JSON, nullable=True)   # 전체 작업 단계 목록
    current_step = db.Column(db.Text, nullable=True)    # 작업 중인 단계
    status = db.Column(ENUM('undone', 'doing', 'done', name='auto_task_status_enum'), nullable=False, default='undone')
    content = db.Column(db.JSON, nullable=True)
    priority = db.Column(db.Integer, nullable=True)
    meta = db.Column(db.JSON, nullable=True)

    # 관계 설정 (User와 연결)
    auto_task_steps = db.relationship('AutoTaskStep', back_populates='auto_task', cascade='all, delete-orphan', lazy="select")
    user = db.relationship('User', back_populates='auto_tasks')