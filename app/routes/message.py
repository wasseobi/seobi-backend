from flask import request
from flask_restx import Resource, Namespace, fields
from app.models import db, Message, Session
from app.utils.openai_client import get_openai_client, get_completion
from app import api
import uuid

# Create namespace
ns = Namespace('messages', description='Message operations for chat with AI')

# Define models for documentation
message_model = ns.model('Message', {
    'id': fields.String(readonly=True, description='Message UUID', example='123e4567-e89b-12d3-a456-426614174000'),
    'session_id': fields.String(required=True, description='Session UUID', example='123e4567-e89b-12d3-a456-426614174000'),
    'user_id': fields.String(required=True, description='User UUID', example='123e4567-e89b-12d3-a456-426614174000'),
    'content': fields.String(required=True, description='Message content', example='안녕하세요, 도움이 필요합니다.'),
    'role': fields.String(required=True, description='Message role (user/assistant/system/tool)', example='user', enum=['user', 'assistant', 'system', 'tool']),
    'timestamp': fields.DateTime(readonly=True, description='Creation timestamp'),
    'vector': fields.List(fields.Float, description='Message vector embedding', required=False)
})

message_input = ns.model('MessageInput', {
    'session_id': fields.String(required=True, description='Session UUID', example='123e4567-e89b-12d3-a456-426614174000'),
    'user_id': fields.String(required=True, description='User UUID', example='123e4567-e89b-12d3-a456-426614174000'),
    'content': fields.String(required=True, description='Message content', example='파이썬으로 웹 서버를 만드는 방법을 알려주세요.'),
    'role': fields.String(required=True, description='Message role', example='user', enum=['user', 'assistant', 'system', 'tool'])
})

message_update = ns.model('MessageUpdate', {
    'content': fields.String(description='Message content'),
    'role': fields.String(description='Message role (user/assistant/system/tool)')
})

completion_input = ns.model('CompletionInput', {
    'user_id': fields.String(required=True, description='User UUID', example='123e4567-e89b-12d3-a456-426614174000'),
    'content': fields.String(required=True, description='Message to send to AI', example='파이썬으로 웹 서버를 만드는 방법을 알려주세요.')
})

completion_response = ns.model('CompletionResponse', {
    'user_message': fields.Nested(message_model, description='The user message that was sent'),
    'assistant_message': fields.Nested(message_model, description='The AI assistant\'s response')
})

@ns.route('/session/<uuid:session_id>')
@ns.param('session_id', 'The session identifier')
@ns.response(404, 'Session not found')
class SessionMessageList(Resource):
    @ns.doc('list_session_messages',
            description='Get all messages in a session, ordered by timestamp')
    @ns.marshal_list_with(message_model)
    def get(self, session_id):
        """List all messages in a session"""
        session = Session.query.get_or_404(session_id)
        return Message.query.filter_by(session_id=session_id).order_by(Message.timestamp.asc()).all()

    @ns.doc('create_message',
            description='Create a new message in a session. Use this for system messages or manual message creation.')
    @ns.expect(message_input)
    @ns.marshal_with(message_model, code=201)
    @ns.response(400, 'Invalid input or session is finished')
    def post(self, session_id):
        """Create a new message in a session"""
        # Validate session
        session = Session.query.get_or_404(session_id)
        if session.finish_at:
            ns.abort(400, 'Cannot add message to finished session')
            
        data = request.json
        if not data or 'content' not in data:
            ns.abort(400, 'Message content is required')
            
        try:
            message = Message(
                session_id=session_id,
                user_id=data['user_id'],
                content=data['content'],
                role=data.get('role', 'user')
            )
            db.session.add(message)
            db.session.commit()
            return message, 201
            
        except Exception as e:
            db.session.rollback()
            ns.abort(500, str(e))

def update_session_title_description(session_id: str, user_message: str, assistant_message: str) -> None:
    """Update session title and description based on first conversation"""
    try:
        # Prepare messages for title/description generation
        context_messages = [
            {"role": "system", "content": "다음 대화를 바탕으로 세션의 제목과 설명을 생성해주세요. "
                                        "제목은 20자 이내로, 설명은 100자 이내로 작성해주세요. "
                                        "응답은 JSON 형식으로 'title'과 'description' 키를 포함해야 합니다."},
            {"role": "user", "content": "다음 대화를 바탕으로 세션의 제목과 설명을 생성해주세요:\n\n"
                                      f"user: {user_message}\n"
                                      f"assistant: {assistant_message}"}
        ]

        # Get title and description from AI
        client = get_openai_client()
        response = get_completion(client, context_messages)
        
        # Parse response and update session
        import json
        try:
            result = json.loads(response)
            session = Session.query.get(session_id)
            if session and 'title' in result and 'description' in result:
                session.title = result['title']
                session.description = result['description']
                db.session.commit()
        except json.JSONDecodeError:
            # If response is not valid JSON, use it as description
            session = Session.query.get(session_id)
            if session:
                session.description = response[:100]  # Truncate to 100 characters
                db.session.commit()
    except Exception as e:
        # Log error but don't fail the request
        print(f"Failed to update session title/description: {str(e)}")

@ns.route('/session/<uuid:session_id>/completion')
@ns.param('session_id', 'The session identifier')
@ns.response(404, 'Session not found')
@ns.response(400, 'Invalid input or session is finished')
@ns.response(500, 'Failed to get AI completion')
class MessageCompletion(Resource):
    @ns.doc('create_completion',
            description='Send a message to the AI and get a response. This will:\n'
                      '1. Save your message\n'
                      '2. Get AI response\n'
                      '3. Save AI response\n'
                      '4. Update session title/description if this is the first message\n'
                      '5. Return both messages')
    @ns.expect(completion_input)
    @ns.marshal_with(completion_response)
    def post(self, session_id):
        """Create a new message and get AI completion"""
        try:
            # Validate session
            session = Session.query.get_or_404(session_id)
            if session.finish_at:
                ns.abort(400, 'Cannot add message to finished session')
                
            data = request.json
            if not data or 'content' not in data:
                ns.abort(400, 'Message content is required')

            # Create user message
            user_message = Message(
                session_id=session_id,
                user_id=data['user_id'],
                role='user',
                content=data['content']
            )
            db.session.add(user_message)
            db.session.flush()

            # Get conversation history
            previous_messages = Message.query.filter_by(session_id=session_id).order_by(Message.timestamp.asc()).all()
            history = [
                {"role": msg.role, "content": msg.content}
                for msg in previous_messages
            ]

            # Prepare messages for OpenAI
            messages = [
                {"role": "system", "content": "당신은 도움이 되는 AI 어시스턴트입니다. 응답은 간결하고 명확하게 해주세요."},
                *history,
                {"role": "user", "content": data['content']}
            ]

            # Get AI completion
            try:
                client = get_openai_client()
                response = get_completion(client, messages)
            except Exception as e:
                db.session.rollback()
                ns.abort(500, f"Failed to get AI completion: {str(e)}")

            # Create assistant message
            assistant_message = Message(
                session_id=session_id,
                user_id=data['user_id'],
                role='assistant',
                content=response
            )
            db.session.add(assistant_message)
            db.session.commit()

            # Update session title and description based on conversation
            # Only update if this is the first message in the session (before adding current messages)
            if len(previous_messages) == 1:
                update_session_title_description(session_id, data['content'], response)

            return {
                'user_message': user_message,
                'assistant_message': assistant_message
            }

        except Exception as e:
            db.session.rollback()
            ns.abort(500, str(e))

# Register the namespace
api.add_namespace(ns)