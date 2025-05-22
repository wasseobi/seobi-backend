from flask import request
from flask_restx import Resource, Namespace
from app.schemas.user_schema import register_models
from app.services.user_service import UserService

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
        user = self.user_service.get_user_by_id(user_id)
        if not user:
            ns.abort(404, f"User {user_id} not found")
        
        if self.user_service.delete_user(user_id):
            return '', 204
        ns.abort(500, "Failed to delete user")