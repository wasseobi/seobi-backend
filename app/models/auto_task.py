from app.models.db import db
import uuid
from sqlalchemy.dialects.postgresql import UUID, ENUM
from datetime import datetime, timezone

class AutoTask(db.Model):
    __tablename__ = 'auto_task'
    id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = db.Column(UUID(as_uuid=True), db.ForeignKey('user.id'), nullable=False)

    # 관계 설정 (User와 연결)
    user = db.relationship('User', back_populates='auto_tasks')