from app.models.db import db
import uuid
from sqlalchemy.dialects.postgresql import UUID, ENUM
from datetime import datetime, timezone

class AutoTaskStep(db.Model):
    __tablename__ = 'auto_task_step'
    id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    auto_task_id = db.Column(UUID(as_uuid=True), db.ForeignKey('auto_task.id'), nullable=False) 
    step_id = db.Column(db.Text, nullable=False) # 업무 제목
    objective = db.Column(db.Text, nullable=True) # 업무 설명
    task_list = db.Column(db.JSON, nullable=True) # 종속성이 있는 업무 목록(JSON)
    tool = db.Column(db.Text, nullable=True)
    linked_service = db.Column(db.Text, nullable=True)  # 외부 연동 서비스명 등
    status = db.Column(ENUM('undone', 'done', name='auto_task_steps_status_enum'), nullable=False, default='undone')
    raw = db.Column(db.JSON, nullable=True)
    priority = db.Coumn(db.Integer, nullable=True)
    error = db.Column(db.Text, nullable=True)
    input = db.Column(db.JSON, nullable=True)
    output = db.Column(db.JSON, nullable=True)
    start_at = db.Column(db.DateTime(timezone=True), nullable=True)
    finish_at = db.Column(db.DateTime(timezone=True), nullable=True)
    created_at = db.Column(db.DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)

    # 관계 설정
    auto_task = db.relationship('AutoTask', back_populates='auto_task_steps')

    class AutoTaskStep(db.Model):
        __tablename__ = 'auto_task_step'
        id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
        auto_task_id = db.Column(UUID(as_uuid=True), db.ForeignKey('auto_task.id'), nullable=False)
        title = db.Column(db.Text, nullable=False)
        description = db.Column(db.Text)
        task_list = db.Column(db.JSON, nullable=True)
        tool = db.Column(db.Text, nullable=True)
        linked_service = db.Column(db.Text, nullable=True)
        status = db.Column(ENUM('undone', 'done', 'running', 'failed', name='auto_task_status_enum'), default='undone')
        input = db.Column(db.JSON, nullable=True)
        output = db.Column(db.JSON, nullable=True)
        error = db.Column(db.Text, nullable=True)
        attempt = db.Column(db.Integer, default=0)  # 시도 횟수
        priority = db.Column(db.Integer, nullable=True)
        started_at = db.Column(db.DateTime(timezone=True), nullable=True)
        finished_at = db.Column(db.DateTime(timezone=True), nullable=True)
        created_at = db.Column(db.DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
        # 관계
        auto_task = db.relationship('AutoTask', back_populates='auto_task_steps')