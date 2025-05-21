import os
from flask import Flask, request, abort
from flask_migrate import Migrate
from flask_cors import CORS
from dotenv import load_dotenv

from app.models import db, User, Session, Message, MCPServer, ActiveMCPServer


def create_app():
    load_dotenv()
    app = Flask(__name__)
    app.config.from_object('config.Config')
    db.init_app(app)
    Migrate(app, db)
    CORS(app)

    # Blueprint 등록
    from app.routes.user import user_bp
    from app.routes.session import session_bp
    from app.routes.message import message_bp
    from app.routes.mcp_server import mcp_server_bp
    from app.routes.mcp_server_activation import mcp_server_activation_bp

    app.register_blueprint(user_bp, url_prefix='/users')
    app.register_blueprint(session_bp, url_prefix='/sessions')
    app.register_blueprint(message_bp, url_prefix='/messages')
    app.register_blueprint(mcp_server_bp, url_prefix='/mcp_servers')
    app.register_blueprint(mcp_server_activation_bp,
                           url_prefix='/mcp_server_activations')

    return app
