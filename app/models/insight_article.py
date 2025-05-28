from app.models.db import db
import uuid
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy import Enum, DateTime
from datetime import datetime, timezone

class InsightArticle(db.Model):
    __tablename__ = 'insight_article'
    id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = db.Column(UUID(as_uuid=True), db.ForeignKey('user.id'), nullable=False)
    title = db.Column(db.Text, nullable=False)
    content = db.Column(db.Text, nullable=False)
    tags = db.Column(db.JSON, nullable=True)  # 관련 키워드 리스트
    source = db.Column(db.Text, nullable=False)
    created_at = db.Column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc))
    type = db.Column(Enum('chat', 'report', name='article_type'), nullable=False, default='chat')
    keywords = db.Column(db.JSON, nullable=True)      # 사용된 키워드 리스트
    interest_ids = db.Column(db.JSON, nullable=True)  # 사용된 interest id 리스트

    # 관계 설정
    user = db.relationship('User', back_populates='insight_articles')
