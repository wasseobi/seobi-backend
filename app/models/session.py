from app.models.db import db
import uuid
from sqlalchemy.dialects.postgresql import UUID
from datetime import datetime, timezone


class Session(db.Model):
    __tablename__ = 'session'
    id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = db.Column(UUID(as_uuid=True), db.ForeignKey(
        'user.id'), nullable=False)
    start_at = db.Column(db.DateTime(timezone=True), default=lambda: datetime.now(
        timezone.utc), nullable=False)
    finish_at = db.Column(db.DateTime(timezone=True), nullable=True)
    title = db.Column(db.Text, nullable=True)
    description = db.Column(db.Text, nullable=True)
