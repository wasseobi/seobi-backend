from flask import request
from flask_restx import Resource, Namespace
from app.services.session_service import SessionService
from app.schemas.session_schema import register_models
from app import api
import uuid

# Create namespace
ns = Namespace('sessions', description='Session operations')

# Register models for documentation
session_model, session_input, session_update = register_models(ns)

# Initialize service
session_service = SessionService()

@ns.route('/')
class SessionList(Resource):
    @ns.doc('list_sessions')
    @ns.marshal_list_with(session_model)
    def get(self):
        """List all sessions"""
        return session_service.get_all_sessions()

    @ns.doc('create_session')
    @ns.expect(session_input)
    @ns.marshal_with(session_model, code=201)
    @ns.response(400, 'Invalid input')
    @ns.response(404, 'User not found')
    def post(self):
        """Create a new session"""
        data = request.json
        
        # Validate input
        if not data or 'user_id' not in data:
            ns.abort(400, 'user_id is required')
            
        try:
            session = session_service.create_session(uuid.UUID(data['user_id']))
            return session, 201
        except ValueError as e:
            ns.abort(404, str(e))
        except Exception as e:
            ns.abort(500, str(e))

@ns.route('/<uuid:session_id>')
@ns.param('session_id', 'The session identifier')
@ns.response(404, 'Session not found')
class SessionResource(Resource):
    @ns.doc('get_session')
    @ns.marshal_with(session_model)
    def get(self, session_id):
        """Get a session by ID"""
        try:
            return session_service.get_session(session_id)
        except ValueError as e:
            ns.abort(404, str(e))

    @ns.doc('update_session')
    @ns.expect(session_update)
    @ns.marshal_with(session_model)
    def put(self, session_id):
        """Update a session"""
        try:
            data = request.json
            return session_service.update_session(session_id, **data)
        except ValueError as e:
            ns.abort(404, str(e))

    @ns.doc('delete_session')
    @ns.response(204, 'Session deleted')
    def delete(self, session_id):
        """Delete a session"""
        try:
            session_service.delete_session(session_id)
            return '', 204
        except ValueError as e:
            ns.abort(404, str(e))

@ns.route('/<uuid:session_id>/finish')
@ns.param('session_id', 'The session identifier')
@ns.response(404, 'Session not found')
@ns.response(400, 'Session already finished')
class SessionFinish(Resource):
    @ns.doc('finish_session')
    @ns.marshal_with(session_model)
    def post(self, session_id):
        """Mark a session as finished"""
        try:
            return session_service.finish_session(session_id)
        except ValueError as e:
            if 'already finished' in str(e):
                ns.abort(400, str(e))
            ns.abort(404, str(e))

@ns.route('/user/<uuid:user_id>')
@ns.param('user_id', 'The user identifier')
@ns.response(404, 'User not found')
class UserSessions(Resource):
    @ns.doc('get_user_sessions')
    @ns.marshal_list_with(session_model)
    def get(self, user_id):
        """Get all sessions for a specific user"""
        try:
            return session_service.get_user_sessions(user_id)
        except ValueError as e:
            ns.abort(404, str(e))
        except Exception as e:
            ns.abort(500, str(e))

# Register the namespace
api.add_namespace(ns)