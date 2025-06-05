import os
from flask import Flask
from flask_migrate import Migrate
from flask_cors import CORS
from dotenv import load_dotenv
from flask_restx import Api
from app.models.db import db
from flask_jwt_extended import JWTManager
from app.utils.app_config import init_config

migrate = Migrate()

# Swagger UI에서 사용할 인증 설정
authorizations = {
    'Bearer': {
        'type': 'apiKey',
        'in': 'header',
        'name': 'Authorization',
        'description': "Type in the *'Value'* input box below: **'Bearer &lt;JWT&gt;'**, where JWT is the token"
    }
}

api = Api(
    title='Seobi API',
    version='0.1.0',
    description='Seobi Backend API Documentation',
    doc='/docs',  # Swagger UI will be available at /docs
    authorizations=authorizations,
    security='Bearer'  # 모든 엔드포인트에 기본적으로 Bearer 인증 적용
)

def create_app(config_name=None):
    load_dotenv(override=True)
    app = Flask(__name__)

    # set json encoding to utf-8
    app.json.ensure_ascii = False
    app.json.mimetype = 'application/json; charset=utf-8'
    
    if config_name == 'testing':
        app.config.from_object('config.TestConfig')
    else:
        app.config.from_object('config.Config')

    # Initialize extensions
    db.init_app(app)
    migrate.init_app(app, db)
    CORS(app)
    api.init_app(app)
    JWTManager(app)  # JWT 매니저 등록
    init_config(app)

    # Import models after db initialization
    from app.models.user import User
    from app.models.session import Session
    from app.models.message import Message
    from app.models.mcp_server import MCPServer
    from app.models.mcp_server_activation import ActiveMCPServer

    # Register production namespaces
    from app.routes.auth import ns as auth_ns
    from app.routes.session import ns as session_ns
    from app.routes.message import ns as message_ns

    # Register debug namespaces
    from app.routes.debug.user import ns as debug_user_ns
    from app.routes.debug.session import ns as debug_session_ns
    from app.routes.debug.message import ns as debug_message_ns
    from app.routes.debug.mcp_server import ns as debug_mcp_server_ns
    from app.routes.debug.mcp_server_activation import ns as debug_mcp_server_activation_ns
    from app.routes.debug.schedule import ns as debug_schedule_ns
    from app.routes.debug.report import ns as debug_report_ns
    from app.routes.debug.auto_task import ns as debug_auto_task_ns

    # Add production namespaces
    api.add_namespace(auth_ns)  # /sign, /verify
    api.add_namespace(session_ns)  # /s/*
    api.add_namespace(message_ns)  # /m/*

    # Add debug namespaces with prefix
    api.add_namespace(debug_user_ns, path='/debug/users')
    api.add_namespace(debug_session_ns, path='/debug/sessions')
    api.add_namespace(debug_message_ns, path='/debug/messages')
    api.add_namespace(debug_mcp_server_ns, path='/debug/mcp_servers')
    api.add_namespace(debug_mcp_server_activation_ns, path='/debug/mcp_server_activations')
    api.add_namespace(debug_schedule_ns, path='/debug/schedule')
    api.add_namespace(debug_report_ns, path='/debug/reports')
    api.add_namespace(debug_auto_task_ns, path='/debug/autotask')

    return app
