from flask import Blueprint, request, jsonify
from app.models import User, db

user_bp = Blueprint('user', __name__)

@user_bp.route('', methods=['POST'])
def create_user():
    data = request.json
    username = data.get('username')
    email = data.get('email')
    if not username or not email:
        return jsonify({'error': 'username and email required'}), 400
    if User.query.filter((User.username == username) | (User.email == email)).first():
        return jsonify({'error': 'username or email already exists'}), 409
    user = User(username=username, email=email)
    db.session.add(user)
    db.session.commit()
    return jsonify({'id': str(user.id), 'username': user.username, 'email': user.email}), 201

@user_bp.route('', methods=['GET'])
def get_users():
    users = User.query.all()
    return jsonify([
        {'id': str(u.id), 'username': u.username, 'email': u.email}
        for u in users
    ])

@user_bp.route('/<uuid:user_id>', methods=['GET'])
def get_user(user_id):
    user = User.query.get_or_404(user_id)
    return jsonify({'id': str(user.id), 'username': user.username, 'email': user.email})

@user_bp.route('/<uuid:user_id>', methods=['PUT'])
def update_user(user_id):
    user = User.query.get_or_404(user_id)
    data = request.json
    username = data.get('username')
    email = data.get('email')
    if username:
        user.username = username
    if email:
        user.email = email
    db.session.commit()
    return jsonify({'id': str(user.id), 'username': user.username, 'email': user.email})

@user_bp.route('/<uuid:user_id>', methods=['DELETE'])
def delete_user(user_id):
    user = User.query.get_or_404(user_id)
    db.session.delete(user)
    db.session.commit()
    return '', 204 