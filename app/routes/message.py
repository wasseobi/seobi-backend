"""Message 관련 라우트를 정의하는 모듈입니다."""
from flask import request
from flask_restx import Resource, Namespace
from app.services.message_service import MessageService
from app.schemas.message_schema import register_models
from app import api
import uuid

# Create namespace
ns = Namespace('messages', description='Message operations for chat with AI')

# Register models for documentation
message_model, message_input, message_update, completion_input, completion_response = register_models(
    ns)

message_service = MessageService()


@ns.route('/session/<uuid:session_id>')
@ns.param('session_id', 'The session identifier')
@ns.response(404, 'Session not found')
@ns.response(400, 'Invalid input or session is finished')
class SessionMessageList(Resource):
    @ns.doc('list_session_messages',
            description='Get all messages in a session, ordered by timestamp')
    @ns.marshal_list_with(message_model)
    def get(self, session_id):
        """List all messages in a session"""
        try:
            return message_service.get_session_messages(session_id)
        except ValueError as e:
            ns.abort(400, str(e))

    @ns.doc('create_message',
            description='Create a new message in a session. Use this for system messages or manual message creation.')
    @ns.expect(message_input)
    @ns.marshal_with(message_model, code=201)
    def post(self, session_id):
        """Create a new message in a session"""
        try:
            data = request.json
            if not data or 'content' not in data or 'user_id' not in data:
                ns.abort(400, 'Message content and user_id are required')

            message = message_service.create_message(
                session_id=session_id,
                user_id=data['user_id'],
                content=data['content'],
                role=data.get('role', 'user')
            )
            return message, 201
        except ValueError as e:
            ns.abort(400, str(e))


@ns.route('/session/<uuid:session_id>/langgraph-completion')
@ns.param('session_id', 'The session identifier')
@ns.response(404, 'Session not found')
@ns.response(400, 'Invalid input or session is finished')
@ns.response(500, 'Failed to get AI completion')
class MessageLangGraphCompletion(Resource):
    @ns.doc('create_langgraph_completion',
            description='Send a message to the AI via LangGraph and get a response. This will:\n'
            '1. Save your message\n'
            '2. Get AI response via LangGraph\n'
            '3. Save AI response\n'
            '4. Return both messages')
    @ns.expect(completion_input)
    @ns.marshal_with(completion_response)
    def post(self, session_id):
        try:
            data = request.json
            if not data or 'content' not in data or 'user_id' not in data:
                ns.abort(400, 'Message content and user_id are required')

            result = message_service.create_langgraph_completion(
                session_id=session_id,
                user_id=data['user_id'],
                content=data['content']
            )
            return result
        except ValueError as e:
            ns.abort(400, str(e))


@ns.route('/user/<uuid:user_id>')
@ns.param('user_id', 'The user identifier')
@ns.response(404, 'User not found')
class UserMessages(Resource):
    @ns.doc('get_user_messages')
    @ns.marshal_list_with(message_model)
    def get(self, user_id):
        """Get all messages for a specific user"""
        try:
            return message_service.get_user_messages(user_id)
        except ValueError as e:
            ns.abort(404, str(e))
        except Exception as e:
            ns.abort(500, str(e))


# Register the namespace
api.add_namespace(ns)
