from app.models.db import db
import uuid
from sqlalchemy.dialects.postgresql import UUID, JSONB

class User(db.Model):
    __tablename__ = 'user'
    id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    username = db.Column(db.String(30), nullable=False, unique=True)
    email = db.Column(db.String(255), nullable=False, unique=True)
    user_memory = db.Column(JSONB, nullable=True)

    # Relationships
    sessions = db.relationship('Session', back_populates='user', cascade='all, delete-orphan', lazy="joined")
    messages = db.relationship('Message', back_populates='user', cascade='all, delete-orphan', lazy="select")
    schedules = db.relationship('Schedule', back_populates='user', cascade='all, delete-orphan', lazy=True)
    reports = db.relationship('Report', back_populates='user', cascade='all, delete-orphan', lazy=True)
    insight_articles = db.relationship('InsightArticle', back_populates='user', cascade='all, delete-orphan', lazy=True)
    interests = db.relationship('Interest', back_populates='user', cascade='all, delete-orphan', lazy="joined")
    auto_tasks = db.relationship('AutoTask', back_populates='user', cascade='all, delete-orphan', lazy="select")
    briefings = db.relationship('Briefing', back_populates='user', cascade='all, delete-orphan', lazy=True)
