from app.models.db import db
import uuid
from sqlalchemy.dialects.postgresql import UUID


class User(db.Model):
    __tablename__ = 'user'
    id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    username = db.Column(db.String(30), nullable=False, unique=True)
    email = db.Column(db.String(255), nullable=False, unique=True)

    # Relationships
    sessions = db.relationship('Session', back_populates='user', lazy=True)
    messages = db.relationship('Message', back_populates='user', lazy=True)
