from app.models.db import db
import uuid
from sqlalchemy.dialects.postgresql import UUID, ENUM

class Report(db.Model):
    __tablename__ = 'report'
    id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = db.Column(UUID(as_uuid=True), db.ForeignKey('user.id'), nullable=False)
    schedule_id = db.Column(UUID(as_uuid=True), db.ForeignKey('schedule.id'), nullable=False)
    content = db.Column(db.Text, nullable=True)
    type = db.Column(ENUM('daily', 'weekly', 'monthly', name='report_type_enum'), nullable=False)

    # 관계 설정
    user = db.relationship('User', back_populates='reports')
    schedule = db.relationship('Schedule', back_populates='reports')
