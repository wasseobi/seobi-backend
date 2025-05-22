from app import db
from sqlalchemy.dialects.postgresql import UUID
from datetime import datetime
# pgvector Vector 타입 import (1536차원은 Azure OpenAI text-embedding-ada-002 기준)
try:
    from pgvector.sqlalchemy import Vector
    VECTOR_TYPE = Vector(1536)  # 임베딩 차원에 맞게 수정 (예: 1536)
except ImportError:
    VECTOR_TYPE = db.ARRAY(db.Float)  # pgvector 미설치 시 fallback


class Message(db.Model):
    """
    Message 테이블 모델
    - vector 컬럼은 pgvector(Vector) 또는 ARRAY(Float) 타입
    - 실제 임베딩 차원에 맞게 Vector(차원) 지정 필요
    """
    __tablename__ = 'message'
    id = db.Column(UUID(as_uuid=True), primary_key=True, default=db.func.uuid_generate_v4())
    session_id = db.Column(UUID(as_uuid=True), db.ForeignKey('session.id'), nullable=False)
    user_id = db.Column(UUID(as_uuid=True), db.ForeignKey('user.id'), nullable=False)
    content = db.Column(db.Text, nullable=False)
    role = db.Column(db.String(20), nullable=False, default='user')
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    # 벡터 컬럼 추가 (pgvector or ARRAY)
    vector = db.Column(VECTOR_TYPE)

    def __repr__(self):
        return f'<Message {self.id}>'

    # Relationships
    session = db.relationship('Session', back_populates='messages')
    user = db.relationship('User', back_populates='messages')