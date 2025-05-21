from flask import request
from flask_restx import Resource, Namespace, fields
from app.models.db import db
from app.models.user import User
from app import api

# Create namespace
ns = Namespace('users', description='User operations')

# Define input model for documentation
user_input = ns.model('UserInput', {
    'username': fields.String(required=True, description='Username', example='testuser'),
    'email': fields.String(required=True, description='Email address', example='test@example.com')
})

# Automatically create response model from User class
user_model = ns.model('User', {
    'id': fields.String(description='User UUID', attribute='id'),
    'username': fields.String(required=True, description='Username'),
    'email': fields.String(required=True, description='Email address')
})

@ns.route('/')
class UserList(Resource):
    @ns.doc('list_users')
    @ns.marshal_list_with(user_model)
    def get(self):
        """List all users"""
        return User.query.all()

    @ns.doc('create_user')
    @ns.expect(user_input)
    @ns.marshal_with(user_model, code=201)
    def post(self):
        """Create a new user"""
        data = request.json
        user = User(
            username=data['username'],
            email=data['email']
        )
        user.set_password(data['password'])
        db.session.add(user)
        db.session.commit()
        return user, 201

@ns.route('/<uuid:id>')
@ns.param('id', 'The user identifier')
@ns.response(404, 'User not found')
class UserResource(Resource):
    @ns.doc('get_user')
    @ns.marshal_with(user_model)
    def get(self, id):
        """Get a user by ID"""
        user = User.query.get_or_404(id)
        return user

    @ns.doc('update_user')
    @ns.expect(user_input)
    @ns.marshal_with(user_model)
    def put(self, id):
        """Update a user"""
        user = User.query.get_or_404(id)
        data = request.json
        user.username = data.get('username', user.username)
        user.email = data.get('email', user.email)
        if 'password' in data:
            user.set_password(data['password'])
        db.session.commit()
        return user

    @ns.doc('delete_user')
    @ns.response(204, 'User deleted')
    def delete(self, id):
        """Delete a user"""
        user = User.query.get_or_404(id)
        db.session.delete(user)
        db.session.commit()
        return '', 204

# Register the namespace
api.add_namespace(ns)