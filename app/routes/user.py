import google.auth.transport.requests
import google.oauth2.id_token

from app import api
from app.models.db import db
from app.models.user import User
from app.services.user_service import UserService
from app.schemas.user_schema import register_models

from flask import request, jsonify
from flask_restx import Resource, Namespace, fields
from flask_jwt_extended import create_access_token

# Create namespace
ns = Namespace('users', description='User operations')
user_create, user_update, user_response = register_models(ns)


@ns.route('/')
class UserList(Resource):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.user_service = UserService()

    @ns.doc('list_users')
    @ns.marshal_list_with(user_response)
    def get(self):
        """List all users"""
        return self.user_service.get_all_users()

    @ns.doc('create_user')
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

    @ns.doc('get_user')
    @ns.marshal_with(user_response)
    def get(self, user_id):
        """Get a user by ID"""
        user = self.user_service.get_user_by_id(user_id)
        if not user:
            ns.abort(404, f"User {user_id} not found")
        return user

    @ns.doc('update_user')
    @ns.expect(user_update)
    @ns.marshal_with(user_response)
    def put(self, user_id):
        """Update a user"""
        user = self.user_service.get_user_by_id(user_id)
        if not user:
            ns.abort(404, f"User {user_id} not found")

        data = request.json
        try:
            return self.user_service.update_user(
                user_id=user_id,
                username=data.get('username'),
                email=data.get('email')
            )
        except ValueError as e:
            ns.abort(400, str(e))

    @ns.doc('delete_user')
    @ns.response(204, 'User deleted')
    def delete(self, user_id):
        """Delete a user"""
        user = User.query.get_or_404(id)
        db.session.delete(user)
        db.session.commit()
        return '', 204


@ns.route('/login')
class UserLogin(Resource):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.user_service = UserService()

    @ns.doc('login')
    def post(self):
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
