import uuid

from datetime import datetime, timezone
from sqlalchemy.dialects.postgresql import UUID, ENUM, JSON

from app.models.db import db

class Report(db.Model):
    __tablename__ = 'report'
    id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = db.Column(UUID(as_uuid=True), db.ForeignKey('user.id'), nullable=False)
    content = db.Column(JSON, nullable=False)
    type = db.Column(ENUM('daily', 'weekly', 'monthly', name='report_type_enum'), nullable=False)
    created_at = db.Column(db.DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc))

    # 관계 설정
    user = db.relationship('User', back_populates='reports')