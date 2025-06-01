from app.models.db import db
import uuid
from sqlalchemy.dialects.postgresql import UUID, ENUM
from datetime import datetime, timezone

class AutoTask(db.Model):
    __tablename__ = 'auto_task'
    id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = db.Column(UUID(as_uuid=True), db.ForeignKey('user.id'), nullable=False)
    title = db.Column(db.Text, nullable=False)
    repeat = db.Column(db.Text, nullable=True)  # cron 표현식 등 반복 일정 관리
    created_at = db.Column(db.DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
    start_at = db.Column(db.DateTime(timezone=True), nullable=True)
    finish_at = db.Column(db.DateTime(timezone=True), nullable=True)
    tool = db.Column(db.Text, nullable=False)
    status = db.Column(ENUM('undone', 'done', name='auto_task_status_enum'), nullable=False, default='undone')
    linked_service = db.Column(db.Text, nullable=True)  # 외부 연동 서비스명 등

    # 관계 설정 (User와 연결)
    user = db.relationship('User', back_populates='auto_tasks')