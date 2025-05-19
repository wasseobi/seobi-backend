from models.db import db
from sqlalchemy.dialects.postgresql import ARRAY


class MCPServer(db.Model):
    __tablename__ = 'mcp_server'
    id = db.Column(db.String(64), primary_key=True)
    name = db.Column(db.String(255), nullable=True)
    command = db.Column(db.String(255), nullable=True)
    arguments = db.Column(ARRAY(db.Text), nullable=True)
    required_envs = db.Column(ARRAY(db.Text), nullable=True)
