from flask import request
from flask_restx import Resource, Namespace, fields
from app.models import db, Session
from app import api

# Create namespace
ns = Namespace('sessions', description='Session operations')

# Define models for documentation
session_model = ns.model('Session', {
    'id': fields.Integer(readonly=True, description='Session identifier'),
    'user_id': fields.Integer(required=True, description='User identifier'),
    'created_at': fields.DateTime(readonly=True, description='Creation timestamp'),
    'expires_at': fields.DateTime(required=True, description='Expiration timestamp')
})

session_input = ns.model('SessionInput', {
    'user_id': fields.Integer(required=True, description='User identifier'),
    'expires_at': fields.DateTime(required=True, description='Expiration timestamp')
})

@ns.route('/')
class SessionList(Resource):
    @ns.doc('list_sessions')
    @ns.marshal_list_with(session_model)
    def get(self):
        """List all sessions"""
        return Session.query.all()

    @ns.doc('create_session')
    @ns.expect(session_input)
    @ns.marshal_with(session_model, code=201)
    def post(self):
        """Create a new session"""
        data = request.json
        session = Session(
            user_id=data['user_id'],
            expires_at=data['expires_at']
        )
        db.session.add(session)
        db.session.commit()
        return session, 201

@ns.route('/<int:id>')
@ns.param('id', 'The session identifier')
@ns.response(404, 'Session not found')
class SessionResource(Resource):
    @ns.doc('get_session')
    @ns.marshal_with(session_model)
    def get(self, id):
        """Get a session by ID"""
        session = Session.query.get_or_404(id)
        return session

    @ns.doc('delete_session')
    @ns.response(204, 'Session deleted')
    def delete(self, id):
        """Delete a session"""
        session = Session.query.get_or_404(id)
        db.session.delete(session)
        db.session.commit()
        return '', 204

# Register the namespace
api.add_namespace(ns) 