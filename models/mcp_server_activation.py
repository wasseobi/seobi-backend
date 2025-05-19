from models.db import db
import uuid
from sqlalchemy.dialects.postgresql import UUID, JSONB


class ActiveMCPServer(db.Model):
    __tablename__ = 'mcp_server_activation'
    id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = db.Column(UUID(as_uuid=True), db.ForeignKey(
        'user.id'), nullable=False)
    mcp_server_id = db.Column(db.String(64), db.ForeignKey(
        'mcp_server.id'), nullable=False)
    name = db.Column(db.Text, nullable=False)
    envs = db.Column(JSONB, nullable=True, default={})
