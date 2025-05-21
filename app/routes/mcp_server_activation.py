from flask import request
from flask_restx import Resource, Namespace, fields
from app.models import db, ActiveMCPServer
from app import api
import uuid

# Create namespace
ns = Namespace('mcp_server_activations', description='MCP Server Activation operations')

# Define models for documentation
activation_model = ns.model('ActiveMCPServer', {
    'id': fields.String(readonly=True, description='Activation UUID'),
    'user_id': fields.String(required=True, description='User UUID'),
    'mcp_server_id': fields.String(required=True, description='MCP Server ID'),
    'name': fields.String(required=True, description='Activation name'),
    'envs': fields.Raw(description='Activation environment variables', required=False)
})

activation_input = ns.model('ActivationInput', {
    'user_id': fields.String(required=True, description='User UUID'),
    'mcp_server_id': fields.String(required=True, description='MCP Server ID'),
    'name': fields.String(required=True, description='Activation name'),
    'envs': fields.Raw(description='Activation environment variables', required=False)
})

activation_update = ns.model('ActivationUpdate', {
    'status': fields.String(description='Server status (active/inactive)'),
    'error_message': fields.String(description='Error message if activation failed')
})

@ns.route('')
class ActivationList(Resource):
    @ns.doc('list_activations')
    @ns.marshal_list_with(activation_model)
    def get(self):
        """List all MCP server activations"""
        activations = ActiveMCPServer.query.all()
        return [
            {
                'id': str(activation.id),
                'server_id': str(activation.server_id),
                'status': activation.status,
                'started_at': activation.started_at,
                'ended_at': activation.ended_at,
                'error_message': activation.error_message
            }
            for activation in activations
        ]

    @ns.doc('create_activation')
    @ns.expect(activation_input)
    @ns.marshal_with(activation_model, code=201)
    def post(self):
        """Create a new MCP server activation"""
        data = request.json
        activation = ActiveMCPServer(
            user_id=data['user_id'],
            mcp_server_id=data['mcp_server_id'],
            name=data['name'],
            envs=data.get('envs', {})
        )
        db.session.add(activation)
        db.session.commit()
        return {
            'id': str(activation.id),
            'user_id': str(activation.user_id),
            'mcp_server_id': str(activation.mcp_server_id),
            'name': activation.name,
            'envs': activation.envs
        }, 201

@ns.route('/<uuid:activation_id>')
@ns.param('activation_id', 'The activation identifier (UUID)')
@ns.response(404, 'Activation not found')
class ActivationResource(Resource):
    @ns.doc('get_activation')
    @ns.marshal_with(activation_model)
    def get(self, activation_id):
        """Get an activation by ID"""
        activation = ActiveMCPServer.query.get_or_404(activation_id)
        return {
            'id': str(activation.id),
            'server_id': str(activation.server_id),
            'status': activation.status,
            'started_at': activation.started_at,
            'ended_at': activation.ended_at,
            'error_message': activation.error_message
        }

    @ns.doc('update_activation')
    @ns.expect(activation_update)
    @ns.marshal_with(activation_model)
    def put(self, activation_id):
        """Update an activation"""
        activation = ActiveMCPServer.query.get_or_404(activation_id)
        data = request.json
        if 'status' in data:
            activation.status = data['status']
        if 'error_message' in data:
            activation.error_message = data['error_message']
        db.session.commit()
        return {
            'id': str(activation.id),
            'server_id': str(activation.server_id),
            'status': activation.status,
            'started_at': activation.started_at,
            'ended_at': activation.ended_at,
            'error_message': activation.error_message
        }

    @ns.doc('delete_activation')
    @ns.response(204, 'Activation deleted')
    def delete(self, activation_id):
        """Delete an activation"""
        activation = ActiveMCPServer.query.get_or_404(activation_id)
        db.session.delete(activation)
        db.session.commit()
        return '', 204

# Register the namespace
api.add_namespace(ns)