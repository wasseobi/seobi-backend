from flask import request
from flask_restx import Resource, Namespace, fields
from app.models import db, Message
from app import api
import uuid

# Create namespace
ns = Namespace('messages', description='Message operations')

# Define models for documentation
message_model = ns.model('Message', {
    'id': fields.String(readonly=True, description='Message UUID'),
    'session_id': fields.String(required=True, description='Session UUID'),
    'user_id': fields.String(required=True, description='User UUID'),
    'content': fields.String(description='Message content'),
    'role': fields.String(required=True, description='Message role (user/assistant/system/tool)', example='user'),
    'timestamp': fields.DateTime(readonly=True, description='Creation timestamp'),
    'vector': fields.List(fields.Float, description='Message vector embedding', required=False)
})

message_input = ns.model('MessageInput', {
    'session_id': fields.String(required=True, description='Session UUID'),
    'user_id': fields.String(required=True, description='User UUID'),
    'content': fields.String(description='Message content'),
    'role': fields.String(required=True, description='Message role (user/assistant/system/tool)', example='user')
})

message_update = ns.model('MessageUpdate', {
    'content': fields.String(description='Message content'),
    'role': fields.String(description='Message role (user/assistant/system/tool)')
})

@ns.route('')
class MessageList(Resource):
    @ns.doc('list_messages')
    @ns.marshal_list_with(message_model)
    def get(self):
        """List all messages"""
        messages = Message.query.all()
        return [
            {
                'id': str(m.id),
                'session_id': str(m.session_id),
                'user_id': str(m.user_id),
                'content': m.content,
                'role': m.role,
                'timestamp': m.timestamp,
                'vector': list(m.vector) if m.vector else None
            }
            for m in messages
        ]

    @ns.doc('create_message')
    @ns.expect(message_input)
    @ns.marshal_with(message_model, code=201)
    def post(self):
        """Create a new message"""
        data = request.json
        message = Message(
            session_id=data['session_id'],
            user_id=data['user_id'],
            content=data.get('content'),
            role=data['role']
        )
        db.session.add(message)
        db.session.commit()
        return {
            'id': str(message.id),
            'session_id': str(message.session_id),
            'user_id': str(message.user_id),
            'content': message.content,
            'role': message.role,
            'timestamp': message.timestamp,
            'vector': list(message.vector) if message.vector else None
        }, 201

@ns.route('/<uuid:message_id>')
@ns.param('message_id', 'The message identifier (UUID)')
@ns.response(404, 'Message not found')
class MessageResource(Resource):
    @ns.doc('get_message')
    @ns.marshal_with(message_model)
    def get(self, message_id):
        """Get a message by ID"""
        message = Message.query.get_or_404(message_id)
        return {
            'id': str(message.id),
            'session_id': str(message.session_id),
            'user_id': str(message.user_id),
            'content': message.content,
            'role': message.role,
            'timestamp': message.timestamp,
            'vector': list(message.vector) if message.vector else None
        }

    @ns.doc('update_message')
    @ns.expect(message_update)
    @ns.marshal_with(message_model)
    def put(self, message_id):
        """Update a message"""
        message = Message.query.get_or_404(message_id)
        data = request.json
        if 'content' in data:
            message.content = data['content']
        if 'role' in data:
            message.role = data['role']
        db.session.commit()
        return {
            'id': str(message.id),
            'session_id': str(message.session_id),
            'user_id': str(message.user_id),
            'content': message.content,
            'role': message.role,
            'timestamp': message.timestamp,
            'vector': list(message.vector) if message.vector else None
        }

    @ns.doc('delete_message')
    @ns.response(204, 'Message deleted')
    def delete(self, message_id):
        """Delete a message"""
        message = Message.query.get_or_404(message_id)
        db.session.delete(message)
        db.session.commit()
        return '', 204

# Register the namespace
api.add_namespace(ns)