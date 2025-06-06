from app.models.db import db
import uuid
from sqlalchemy.dialects.postgresql import UUID, ENUM
from datetime import datetime, timezone

class AutoTaskStep(db.Model):
    __tablename__ = 'auto_task_step'
    id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    auto_task_id = db.Column(UUID(as_uuid=True), db.ForeignKey('auto_task.id'), nullable=False) 
    title = db.Column(db.Text, nullable=False) # 단계 (뉴스 요약)
    objective = db.Column(db.Text, nullable=True) # 단계별 목적/설명 (예: 뉴스 요약, 전송 등)
    depends_on = db.Column(db.JSON, nullable=True) # 선행 Step id 배열 (선행작업이 끝나야 실행되는 경우)
    tool = db.Column(db.Text, nullable=True)
    status = db.Column(ENUM('undone', 'doing', 'done', 'failed', 'cancelled', name='auto_task_steps_status'), nullable=False, default='undone')
    input = db.Column(db.JSON, nullable=True)   # 단계별 tool 입력값
    output = db.Column(db.JSON, nullable=True)
    started_at = db.Column(db.DateTime(timezone=True), nullable=True)
    finished_at = db.Column(db.DateTime(timezone=True), nullable=True)
    created_at = db.Column(db.DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
    state = db.Column(db.JSON, nullable=True)

    # 관계 설정
    auto_task = db.relationship('AutoTask', back_populates='auto_task_steps')