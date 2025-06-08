import uuid
from app.models.db import db
from datetime import datetime, timezone
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy import Text, ForeignKey


class Briefing(db.Model):
    __tablename__ = 'briefing'
    id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = db.Column(UUID(as_uuid=True),
                        ForeignKey('user.id'), nullable=False)
    content = db.Column(Text, nullable=False)
    script = db.Column(Text, nullable=True)
    created_at = db.Column(db.DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc))

    user = db.relationship('User', back_populates='briefings')