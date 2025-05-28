import uuid
from app.models.db import db
from datetime import datetime, timezone
from sqlalchemy.dialects.postgresql import UUID, JSON
from sqlalchemy import Column, Text, DateTime, ForeignKey


class Interest(db.Model):
    __tablename__ = 'interest'

    id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = db.Column(UUID(as_uuid=True),
                        ForeignKey('user.id'), nullable=False)
    content = db.Column(Text, nullable=False)
    source_message = db.Column(JSON, nullable=False)  # message_id 리스트
    created_at = db.Column(db.DateTime(
        timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)

    user = db.relationship('User', back_populates='interests')