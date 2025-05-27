from app.models.db import db
import uuid
from sqlalchemy.dialects.postgresql import UUID

class InsightArticle(db.Model):
    __tablename__ = 'insight_article'
    id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = db.Column(UUID(as_uuid=True), db.ForeignKey('user.id'), nullable=False)
    title = db.Column(db.Text, nullable=False)
    content = db.Column(db.Text, nullable=False)
    tags = db.Column(db.JSON, nullable=True)  # 관련 키워드 리스트
    source = db.Column(db.Text, nullable=False)

    # 관계 설정
    user = db.relationship('User', back_populates='insight_articles')
