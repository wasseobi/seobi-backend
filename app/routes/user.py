import google.auth.transport.requests
import google.oauth2.id_token

from app import api
from app.models.db import db
from app.models.user import User
from app.services.user_service import UserService
from app.schemas.user_schema import register_models
from app.utils.auth_middleware import require_auth

from flask import request, jsonify
from flask_restx import Resource, Namespace, fields
from flask_jwt_extended import create_access_token

# Create namespace
ns = Namespace('users', description='User operations')

# Register models for documentation
user_create, user_update, user_response = register_models(ns)

# 네임스페이스 수준에서 인증 설정
ns.security = [{"Bearer": []}]  # 이 네임스페이스의 모든 엔드포인트에 Bearer 인증 적용


@ns.route('/')
class UserList(Resource):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.user_service = UserService()

    @ns.doc('list_users', security='Bearer')  # Swagger UI에 인증 필요 표시
    @ns.marshal_list_with(user_response)
    @require_auth
    def get(self):
        """List all users"""
        return self.user_service.get_all_users()

    @ns.doc('create_user', security=[])  # 인증 불필요 표시
    @ns.expect(user_create)
    @ns.marshal_with(user_response, code=201)
    def post(self):
        """Create a new user"""
        data = request.json
        try:
            return self.user_service.create_user(
                username=data['username'],
                email=data['email']
            ), 201
        except ValueError as e:
            ns.abort(400, str(e))


@ns.route('/<uuid:user_id>')
@ns.param('user_id', 'The user identifier')
@ns.response(404, 'User not found')
class UserResource(Resource):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.user_service = UserService()

    @ns.doc('get_user', security='Bearer')
    @ns.marshal_with(user_response)
    @require_auth
    def get(self, user_id):
        """Fetch a user"""
        return self.user_service.get_user_by_id(user_id)

    @ns.doc('update_user', security='Bearer')
    @ns.expect(user_update)
    @ns.marshal_with(user_response)
    @require_auth
    def put(self, user_id):
        """Update a user"""
        data = request.json
        try:
            return self.user_service.update_user(user_id, data)
        except ValueError as e:
            ns.abort(400, str(e))

    @ns.doc('delete_user', security='Bearer')
    @ns.response(204, 'User deleted')
    @require_auth
    def delete(self, user_id):
        """Delete a user"""
        self.user_service.delete_user(user_id)
        return '', 204


@ns.route('/login')
class UserLogin(Resource):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.user_service = UserService()

    @ns.doc('login', security=[])  # 로그인은 인증 불필요
    def post(self):
        """Login with Google ID token"""
        data = request.json
        id_token = data.get('id_token')
        if not id_token:
            return {'error': 'id_token required'}, 400
        try:
            # 구글 id_token 검증
            request_adapter = google.auth.transport.requests.Request()
            id_info = google.oauth2.id_token.verify_oauth2_token(
                id_token, request_adapter)
            email = id_info.get('email')
            username = id_info.get('name') or (
                email.split('@')[0] if email else None)
            if not email:
                return {'error': 'No email in token'}, 400
            # UserService로 사용자 조회 또는 생성
            user = self.user_service.get_user_by_email(email)
            if not user:
                user = self.user_service.create_user(
                    username=username, email=email)
            # JWT 액세스 토큰 생성 (Flask-JWT-Extended 활용)
            access_token = create_access_token(identity=user['id'], additional_claims={
                'username': user['username'],
                'email': user['email']
            })
            return {
                'access_token': access_token,
                'id': user['id'],
                'username': user['username'],
                'email': user['email']
            }, 200
        except Exception as e:
            return {'error': 'Invalid id_token', 'detail': str(e)}, 401


# Register the namespace
api.add_namespace(ns)
