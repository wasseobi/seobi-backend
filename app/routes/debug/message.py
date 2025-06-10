"""Message 관련 라우트를 정의하는 모듈입니다."""
from flask import request, Response, stream_with_context
from flask_restx import Resource, Namespace, fields
from app.services.message_service import MessageService
from app.schemas.message_schema import register_models
from app.utils.auth_middleware import require_auth
from app import api
import uuid
import json
import asyncio
from functools import partial

# Create namespace
ns = Namespace('messages', description='Message operations for chat with AI')

# Register models for documentation
message_model, message_input, message_update, completion_input, completion_response = register_models(
    ns)

message_service = MessageService()

vector_search_time_model = ns.model('VectorSearchByTimeInput', {
    'user_id': fields.String(required=True, description='User ID', example='03823edc-9d2e-4040-b104-1d958bcf8013'),
    'query': fields.String(required=True, description='검색 쿼리', example='로건이'),
    'top_k': fields.Integer(required=False, description='Top K', example=5, default=5),
    'start_timestamp': fields.String(required=False, description='검색 시작 시각(ISO8601)', example='2024-05-01T00:00:00+00:00'),
    'end_timestamp': fields.String(required=False, description='검색 종료 시각(ISO8601)', example='2024-05-31T23:59:59+00:00')
})

@ns.route('/session/<uuid:session_id>')
@ns.param('session_id', 'The session identifier')
@ns.response(404, 'Session not found')
@ns.response(400, 'Invalid input or session is finished')
class SessionMessageList(Resource):
    @ns.doc('list_session_messages',
            description='Get all messages in a session, ordered by timestamp')
    @ns.marshal_list_with(message_model)
    @require_auth
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
    @require_auth
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
            description='Send a message to the AI via LangGraph and get a response with streaming support.')
    @ns.expect(ns.model('LangGraphCompletionInput', {
        'content': fields.String(required=True, description='User message content', example='내일 오전 10시에 회의 잡아줘'),
        'user_id': fields.String(required=True, description='User UUID', example='03823edc-9d2e-4040-b104-1d958bcf8013')
    }))
    @ns.marshal_with(completion_response, code=200)
    @require_auth
    def post(self, session_id):
        """Create a completion using LangGraph"""
        try:
            data = request.json
            user_id = data.get('user_id')
            if not data or 'content' not in data or not user_id:
                ns.abort(400, 'Message content and user_id are required')

            # SSE 요청인지 확인
            if request.accept_mimetypes['text/event-stream']:
                def generate():
                    for chunk in message_service.create_langgraph_completion(
                        session_id=session_id,
                        user_id=user_id,
                        content=data['content']
                    ):
                        print("[SSE CHUNK]", json.dumps(chunk, ensure_ascii=False, indent=2))
                        yield json.dumps(chunk, ensure_ascii=False) + "\n"
                return Response(
                    stream_with_context(generate()),
                    mimetype='text/event-stream',
                    headers={
                        'Cache-Control': 'no-cache',
                        'Connection': 'keep-alive'
                    }
                )
            else:
                # Swagger/curl 등 일반 JSON 요청: 모든 chunk를 리스트로 반환
                chunks = list(message_service.create_langgraph_completion(
                    session_id=session_id,
                    user_id=user_id,
                    content=data['content']
                ))
                # 모든 chunk의 content를 합쳐서 answer로 반환
                answer = ''.join(chunk.get('content', '') for chunk in chunks if chunk.get('type') == 'chunk')
                return {"answer": answer, "chunks": chunks}, 200
                
        except ValueError as e:
            ns.abort(400, str(e))
        except Exception as e:
            print("Error in langgraph-completion:", str(e))
            ns.abort(500, str(e))


@ns.route('/user/<uuid:user_id>')
@ns.param('user_id', 'The user identifier')
@ns.response(404, 'User not found')
class UserMessages(Resource):
    @ns.doc('get_user_messages')
    @ns.marshal_list_with(message_model)
    @require_auth
    def get(self, user_id):
        """Get all messages for a specific user"""
        try:
            return message_service.get_user_messages(user_id)
        except ValueError as e:
            ns.abort(404, str(e))
        except Exception as e:
            ns.abort(500, str(e))


@ns.route('/vectors/update')
class MessageVectorUpdate(Resource):
    @ns.doc('update_message_vectors',
            description='Update vectors for existing messages')
    @ns.param('user_id', 'Optional: Update vectors only for specific user')
    @require_auth
    def post(self):
        """기존 메시지들의 벡터를 업데이트합니다."""
        try:
            user_id = request.args.get('user_id')
            if user_id:
                user_id = uuid.UUID(user_id)
            
            message_service = MessageService()
            result = message_service.update_message_vectors(user_id)
            return result, 200
            
        except Exception as e:
            return {'error': str(e)}, 500


# Register the namespace
api.add_namespace(ns)