from app.models.db import db
import uuid
from pgvector.sqlalchemy import Vector
from sqlalchemy.dialects.postgresql import UUID, ENUM
from datetime import datetime, timezone


class Message(db.Model):
    __tablename__ = 'message'
    id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    session_id = db.Column(UUID(as_uuid=True), db.ForeignKey(
        'session.id'), nullable=False)
    user_id = db.Column(UUID(as_uuid=True), db.ForeignKey(
        'user.id'), nullable=False)
    content = db.Column(db.Text, nullable=True)
    role = db.Column(ENUM('user', 'assistant', 'tool', 'system', name='role_enum'),
                     nullable=False)
    timestamp = db.Column(db.DateTime(
        timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
    vector = db.Column(Vector(1536), nullable=True)
    keyword_text = db.Column(db.Text, nullable=True)
    keyword_vector = db.Column(Vector(1536), nullable=True)
    message_metadata = db.Column(db.JSON, nullable=True)  # metadata 대신 message_metadata 사용

    # Relationships
    session = db.relationship('Session', back_populates='messages')
    user = db.relationship('User', back_populates='messages')