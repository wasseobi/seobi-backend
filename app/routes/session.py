from flask import request
from flask_restx import Resource, Namespace, fields
from app.models import db, Session, User
from datetime import datetime
import uuid
from app import api

# Create namespace
ns = Namespace('sessions', description='Session operations')

# Define models for documentation
session_model = ns.model('Session', {
    'id': fields.String(readonly=True, description='Session UUID'),
    'user_id': fields.String(required=True, description='User UUID'),
    'start_at': fields.DateTime(readonly=True, description='Session start time'),
    'finish_at': fields.DateTime(description='Session finish time', required=False),
    'title': fields.String(description='Session title', required=False),
    'description': fields.String(description='Session description', required=False)
})

session_input = ns.model('SessionInput', {
    'user_id': fields.String(required=True, description='User UUID')
})

session_update = ns.model('SessionUpdate', {
    'title': fields.String(description='Session title'),
    'description': fields.String(description='Session description'),
    'finish_at': fields.DateTime(description='Session finish time')
})

@ns.route('/')
class SessionList(Resource):
    @ns.doc('list_sessions')
    @ns.marshal_list_with(session_model)
    def get(self):
        """List all sessions"""
        return Session.query.order_by(Session.start_at.desc()).all()

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
            
        user_id = data['user_id']
        
        # Verify user exists
        user = User.query.get(user_id)
        if not user:
            ns.abort(404, 'User not found')
            
        try:
            # Create session with default values
            session = Session(
                user_id=user_id,
                title=f"New Session {datetime.utcnow().strftime('%Y-%m-%d %H:%M')}",
                description="Session created"
            )
            db.session.add(session)
            db.session.commit()
            
            return session, 201
            
        except Exception as e:
            db.session.rollback()
            ns.abort(500, str(e))

@ns.route('/<uuid:session_id>')
@ns.param('session_id', 'The session identifier')
@ns.response(404, 'Session not found')
class SessionResource(Resource):
    @ns.doc('get_session')
    @ns.marshal_with(session_model)
    def get(self, session_id):
        """Get a session by ID"""
        return Session.query.get_or_404(session_id)

    @ns.doc('update_session')
    @ns.expect(session_update)
    @ns.marshal_with(session_model)
    def put(self, session_id):
        """Update a session"""
        session = Session.query.get_or_404(session_id)
        data = request.json
        
        if 'title' in data:
            session.title = data['title']
        if 'description' in data:
            session.description = data['description']
        if 'finish_at' in data:
            session.finish_at = data['finish_at']
            
        db.session.commit()
        return session

    @ns.doc('delete_session')
    @ns.response(204, 'Session deleted')
    def delete(self, session_id):
        """Delete a session"""
        session = Session.query.get_or_404(session_id)
        db.session.delete(session)
        db.session.commit()
        return '', 204

@ns.route('/<uuid:session_id>/finish')
@ns.param('session_id', 'The session identifier')
@ns.response(404, 'Session not found')
@ns.response(400, 'Session already finished')
class SessionFinish(Resource):
    @ns.doc('finish_session')
    @ns.marshal_with(session_model)
    def post(self, session_id):
        """Mark a session as finished"""
        session = Session.query.get_or_404(session_id)
        
        if session.finish_at:
            ns.abort(400, 'Session is already finished')
            
        session.finish_at = datetime.utcnow()
        db.session.commit()
        return session

# Register the namespace
api.add_namespace(ns)