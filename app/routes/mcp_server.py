from flask import Blueprint, request, jsonify
from app.models import MCPServer, db

mcp_server_bp = Blueprint('mcp_server', __name__)

@mcp_server_bp.route('', methods=['POST'])
def create_mcp_server():
    data = request.json
    id = data.get('id')
    name = data.get('name')
    command = data.get('command')
    arguments = data.get('arguments')
    required_envs = data.get('required_envs')
    mcp_server = MCPServer(id=id, name=name, command=command, arguments=arguments, required_envs=required_envs)
    db.session.add(mcp_server)
    db.session.commit()
    return jsonify({'id': mcp_server.id, 'name': mcp_server.name, 'command': mcp_server.command, 'arguments': mcp_server.arguments, 'required_envs': mcp_server.required_envs}), 201

@mcp_server_bp.route('', methods=['GET'])
def get_mcp_servers():
    servers = MCPServer.query.all()
    return jsonify([
        {'id': s.id, 'name': s.name, 'command': s.command, 'arguments': s.arguments, 'required_envs': s.required_envs}
        for s in servers
    ])

@mcp_server_bp.route('/<string:server_id>', methods=['GET'])
def get_mcp_server(server_id):
    server = MCPServer.query.get_or_404(server_id)
    return jsonify({'id': server.id, 'name': server.name, 'command': server.command, 'arguments': server.arguments, 'required_envs': server.required_envs})

@mcp_server_bp.route('/<string:server_id>', methods=['PUT'])
def update_mcp_server(server_id):
    server = MCPServer.query.get_or_404(server_id)
    data = request.json
    server.name = data.get('name', server.name)
    server.command = data.get('command', server.command)
    server.arguments = data.get('arguments', server.arguments)
    server.required_envs = data.get('required_envs', server.required_envs)
    db.session.commit()
    return jsonify({'id': server.id, 'name': server.name, 'command': server.command, 'arguments': server.arguments, 'required_envs': server.required_envs})

@mcp_server_bp.route('/<string:server_id>', methods=['DELETE'])
def delete_mcp_server(server_id):
    server = MCPServer.query.get_or_404(server_id)
    db.session.delete(server)
    db.session.commit()
    return '', 204 