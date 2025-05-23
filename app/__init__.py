import os
from flask import Flask
from flask_migrate import Migrate
from flask_cors import CORS
from dotenv import load_dotenv
from flask_restx import Api
from app.models.db import db
from flask_jwt_extended import JWTManager

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

def create_app():
    load_dotenv()
    app = Flask(__name__)

    # set json encoding to utf-8
    app.json.ensure_ascii = False
    app.json.mimetype = 'application/json; charset=utf-8'
    

    app.config.from_object('config.Config')

    # Initialize extensions
    db.init_app(app)
    migrate.init_app(app, db)
    CORS(app)
    api.init_app(app)
    JWTManager(app)  # JWT 매니저 등록

    # Import models after db initialization
    from app.models.user import User
    from app.models.session import Session
    from app.models.message import Message
    from app.models.mcp_server import MCPServer
    from app.models.mcp_server_activation import ActiveMCPServer

    # Register namespaces
    from app.routes.user import ns as user_ns
    from app.routes.session import ns as session_ns
    from app.routes.message import ns as message_ns
    from app.routes.mcp_server import ns as mcp_server_ns
    from app.routes.mcp_server_activation import ns as mcp_server_activation_ns

    api.add_namespace(user_ns, path='/users')
    api.add_namespace(session_ns, path='/sessions')
    api.add_namespace(message_ns, path='/messages')
    api.add_namespace(mcp_server_ns, path='/mcp_servers')
    api.add_namespace(mcp_server_activation_ns, path='/mcp_server_activations')

    return app
