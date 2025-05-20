from flask import Blueprint, request, jsonify
from app.models import ActiveMCPServer, db

mcp_server_activation_bp = Blueprint('mcp_server_activation', __name__)

@mcp_server_activation_bp.route('', methods=['POST'])
def create_activation():
    data = request.json
    user_id = data.get('user_id')
    mcp_server_id = data.get('mcp_server_id')
    name = data.get('name')
    envs = data.get('envs')
    activation = ActiveMCPServer(user_id=user_id, mcp_server_id=mcp_server_id, name=name, envs=envs)
    db.session.add(activation)
    db.session.commit()
    return jsonify({'id': str(activation.id), 'user_id': str(activation.user_id), 'mcp_server_id': activation.mcp_server_id, 'name': activation.name, 'envs': activation.envs}), 201

@mcp_server_activation_bp.route('', methods=['GET'])
def get_activations():
    activations = ActiveMCPServer.query.all()
    return jsonify([
        {'id': str(a.id), 'user_id': str(a.user_id), 'mcp_server_id': a.mcp_server_id, 'name': a.name, 'envs': a.envs}
        for a in activations
    ])

@mcp_server_activation_bp.route('/<uuid:activation_id>', methods=['GET'])
def get_activation(activation_id):
    activation = ActiveMCPServer.query.get_or_404(activation_id)
    return jsonify({'id': str(activation.id), 'user_id': str(activation.user_id), 'mcp_server_id': activation.mcp_server_id, 'name': activation.name, 'envs': activation.envs})

@mcp_server_activation_bp.route('/<uuid:activation_id>', methods=['PUT'])
def update_activation(activation_id):
    activation = ActiveMCPServer.query.get_or_404(activation_id)
    data = request.json
    activation.name = data.get('name', activation.name)
    activation.envs = data.get('envs', activation.envs)
    db.session.commit()
    return jsonify({'id': str(activation.id), 'user_id': str(activation.user_id), 'mcp_server_id': activation.mcp_server_id, 'name': activation.name, 'envs': activation.envs})

@mcp_server_activation_bp.route('/<uuid:activation_id>', methods=['DELETE'])
def delete_activation(activation_id):
    activation = ActiveMCPServer.query.get_or_404(activation_id)
    db.session.delete(activation)
    db.session.commit()
    return '', 204 