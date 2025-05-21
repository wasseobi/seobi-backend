from flask import request
from flask_restx import Resource, Namespace, fields
from app.models import db, MCPServer
from app import api
import uuid

# Create namespace
ns = Namespace('mcp_servers', description='MCP Server operations')

# Define models for documentation
mcp_server_model = ns.model('MCPServer', {
    'id': fields.String(readonly=True, description='Server ID'),
    'name': fields.String(description='Server name', required=False),
    'command': fields.String(description='Command', required=False),
    'arguments': fields.List(fields.String, description='Command arguments', required=False),
    'required_envs': fields.List(fields.String, description='Required environment variables', required=False)
})

mcp_server_input = ns.model('MCPServerInput', {
    'id': fields.String(required=True, description='Server ID'),
    'name': fields.String(description='Server name', required=False),
    'command': fields.String(description='Command', required=False),
    'arguments': fields.List(fields.String, description='Command arguments', required=False),
    'required_envs': fields.List(fields.String, description='Required environment variables', required=False)
})

mcp_server_update = ns.model('MCPServerUpdate', {
    'name': fields.String(description='Server name'),
    'command': fields.String(description='Command'),
    'arguments': fields.List(fields.String, description='Command arguments'),
    'required_envs': fields.List(fields.String, description='Required environment variables')
})

@ns.route('')
class MCPServerList(Resource):
    @ns.doc('list_mcp_servers')
    @ns.marshal_list_with(mcp_server_model)
    def get(self):
        """List all MCP servers"""
        servers = MCPServer.query.all()
        return [
            {
                'id': str(server.id),
                'name': server.name,
                'host': server.host,
                'port': server.port,
                'created_at': server.created_at,
                'updated_at': server.updated_at
            }
            for server in servers
        ]

    @ns.doc('create_mcp_server')
    @ns.expect(mcp_server_input)
    @ns.marshal_with(mcp_server_model, code=201)
    def post(self):
        """Create a new MCP server"""
        data = request.json
        server = MCPServer(
            id=data['id'],
            name=data.get('name'),
            command=data.get('command'),
            arguments=data.get('arguments'),
            required_envs=data.get('required_envs')
        )
        db.session.add(server)
        db.session.commit()
        return {
            'id': str(server.id),
            'name': server.name,
            'command': server.command,
            'arguments': server.arguments,
            'required_envs': server.required_envs
        }, 201

@ns.route('/<uuid:server_id>')
@ns.param('server_id', 'The MCP server identifier (UUID)')
@ns.response(404, 'MCP server not found')
class MCPServerResource(Resource):
    @ns.doc('get_mcp_server')
    @ns.marshal_with(mcp_server_model)
    def get(self, server_id):
        """Get an MCP server by ID"""
        server = MCPServer.query.get_or_404(server_id)
        return {
            'id': str(server.id),
            'name': server.name,
            'host': server.host,
            'port': server.port,
            'created_at': server.created_at,
            'updated_at': server.updated_at
        }

    @ns.doc('update_mcp_server')
    @ns.expect(mcp_server_update)
    @ns.marshal_with(mcp_server_model)
    def put(self, server_id):
        """Update an MCP server"""
        server = MCPServer.query.get_or_404(server_id)
        data = request.json
        if 'name' in data:
            server.name = data['name']
        if 'host' in data:
            server.host = data['host']
        if 'port' in data:
            server.port = data['port']
        db.session.commit()
        return {
            'id': str(server.id),
            'name': server.name,
            'host': server.host,
            'port': server.port,
            'created_at': server.created_at,
            'updated_at': server.updated_at
        }

    @ns.doc('delete_mcp_server')
    @ns.response(204, 'MCP server deleted')
    def delete(self, server_id):
        """Delete an MCP server"""
        server = MCPServer.query.get_or_404(server_id)
        db.session.delete(server)
        db.session.commit()
        return '', 204

# Register the namespace
api.add_namespace(ns)