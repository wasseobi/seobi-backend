from flask import Blueprint, request, jsonify
from app.models import Message, db

message_bp = Blueprint('message', __name__)

@message_bp.route('', methods=['POST'])
def create_message():
    data = request.json
    session_id = data.get('session_id')
    user_id = data.get('user_id')
    content = data.get('content')
    role = data.get('role', 'user')
    message = Message(session_id=session_id, user_id=user_id, content=content, role=role)
    db.session.add(message)
    db.session.commit()
    return jsonify({'id': str(message.id), 'session_id': str(message.session_id), 'user_id': str(message.user_id), 'content': message.content, 'role': message.role, 'timestamp': message.timestamp.isoformat(), 'vector': list(message.vector) if message.vector else None}), 201

@message_bp.route('', methods=['GET'])
def get_messages():
    messages = Message.query.all()
    return jsonify([
        {'id': str(m.id), 'session_id': str(m.session_id), 'user_id': str(m.user_id), 'content': m.content, 'role': m.role, 'timestamp': m.timestamp.isoformat(), 'vector': list(m.vector) if m.vector else None}
        for m in messages
    ])

@message_bp.route('/<uuid:message_id>', methods=['GET'])
def get_message(message_id):
    message = Message.query.get_or_404(message_id)
    return jsonify({'id': str(message.id), 'session_id': str(message.session_id), 'user_id': str(message.user_id), 'content': message.content, 'role': message.role, 'timestamp': message.timestamp.isoformat(), 'vector': list(message.vector) if message.vector else None})

@message_bp.route('/<uuid:message_id>', methods=['PUT'])
def update_message(message_id):
    message = Message.query.get_or_404(message_id)
    data = request.json
    message.content = data.get('content', message.content)
    message.role = data.get('role', message.role)
    db.session.commit()
    return jsonify({'id': str(message.id), 'session_id': str(message.session_id), 'user_id': str(message.user_id), 'content': message.content, 'role': message.role, 'timestamp': message.timestamp.isoformat(), 'vector': list(message.vector) if message.vector else None})

@message_bp.route('/<uuid:message_id>', methods=['DELETE'])
def delete_message(message_id):
    message = Message.query.get_or_404(message_id)
    db.session.delete(message)
    db.session.commit()
    return '', 204 