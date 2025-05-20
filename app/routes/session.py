from flask import Blueprint, request, jsonify
from app.models import Session, db

session_bp = Blueprint('session', __name__)

@session_bp.route('', methods=['POST'])
def create_session():
    data = request.json
    user_id = data.get('user_id')
    title = data.get('title')
    description = data.get('description')
    session = Session(user_id=user_id, title=title, description=description)
    db.session.add(session)
    db.session.commit()
    return jsonify({'id': str(session.id), 'user_id': str(session.user_id), 'title': session.title, 'description': session.description, 'start_at': session.start_at.isoformat(), 'finish_at': session.finish_at.isoformat() if session.finish_at else None}), 201

@session_bp.route('', methods=['GET'])
def get_sessions():
    sessions = Session.query.all()
    return jsonify([
        {'id': str(s.id), 'user_id': str(s.user_id), 'title': s.title, 'description': s.description, 'start_at': s.start_at.isoformat(), 'finish_at': s.finish_at.isoformat() if s.finish_at else None}
        for s in sessions
    ])

@session_bp.route('/<uuid:session_id>', methods=['GET'])
def get_session(session_id):
    session = Session.query.get_or_404(session_id)
    return jsonify({'id': str(session.id), 'user_id': str(session.user_id), 'title': session.title, 'description': session.description, 'start_at': session.start_at.isoformat(), 'finish_at': session.finish_at.isoformat() if session.finish_at else None})

@session_bp.route('/<uuid:session_id>', methods=['PUT'])
def update_session(session_id):
    session = Session.query.get_or_404(session_id)
    data = request.json
    session.title = data.get('title', session.title)
    session.description = data.get('description', session.description)
    session.finish_at = data.get('finish_at', session.finish_at)
    db.session.commit()
    return jsonify({'id': str(session.id), 'user_id': str(session.user_id), 'title': session.title, 'description': session.description, 'start_at': session.start_at.isoformat(), 'finish_at': session.finish_at.isoformat() if session.finish_at else None})

@session_bp.route('/<uuid:session_id>', methods=['DELETE'])
def delete_session(session_id):
    session = Session.query.get_or_404(session_id)
    db.session.delete(session)
    db.session.commit()
    return '', 204 