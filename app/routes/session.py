"""세션 관련 라우트를 정의하는 모듈입니다."""
from flask import request, Response, stream_with_context
from flask_restx import Resource, Namespace, fields
from app.services.session_service import SessionService
from app.services.message_service import MessageService
from app.utils.auth_middleware import require_auth
from config import Config
import uuid
import json
from datetime import datetime

# Create namespace
ns = Namespace('s', description='채팅 세션 및 메시지 작업')

# Define models for documentation
session_response = ns.model('SessionResponse', {
    'session_id': fields.String(description='생성된 세션의 UUID',
                              example='123e4567-e89b-12d3-a456-426614174000')
})

session_close_response = ns.model('SessionCloseResponse', {
    'id': fields.String(description='세션 UUID',
                       example='123e4567-e89b-12d3-a456-426614174000'),
    'user_id': fields.String(description='사용자 UUID',
                           example='123e4567-e89b-12d3-a456-426614174000'),
    'start_at': fields.DateTime(description='세션 시작 시간',
                             example='2025-05-23T09:13:11.475Z'),
    'finish_at': fields.DateTime(description='세션 종료 시간',
                              example='2025-05-23T09:15:11.475Z'),
    'title': fields.String(description='세션 제목',
                         example='AI와의 대화'),
    'description': fields.String(description='세션 설명',
                              example='사용자와 AI의 일반적인 대화')
})

message_send_input = ns.model('MessageSendInput', {
    'content': fields.String(required=True,
                           description='사용자 메시지 내용',
                           example='안녕하세요, 도움이 필요합니다.')
})

session_message_response = ns.model('SessionMessage', {
    'id': fields.String(description='메시지 UUID',
                       example='123e4567-e89b-12d3-a456-426614174000'),
    'session_id': fields.String(description='세션 UUID',
                              example='123e4567-e89b-12d3-a456-426614174000'),
    'user_id': fields.String(description='사용자 UUID',
                           example='123e4567-e89b-12d3-a456-426614174000'),
    'content': fields.String(description='메시지 내용',
                          example='안녕하세요, 도움이 필요합니다.'),
    'role': fields.String(description='메시지 작성자 역할',
                        enum=['user', 'assistant', 'system', 'tool'],
                        example='user'),
    'timestamp': fields.DateTime(description='메시지 작성 시간',
                              example='2025-05-23T09:10:39.366Z'),
    'vector': fields.List(fields.Float, description='메시지 임베딩 벡터',
                        example=[0])
})

# Initialize services
session_service = SessionService()
message_service = MessageService()


@ns.route('/open')
class SessionOpen(Resource):
    @ns.doc('세션 열기',
            description='새로운 채팅 세션을 생성합니다.',
            security='Bearer' if not Config.DEV_MODE else None,
            params={
                'Content-Type': {'description': 'application/json', 'in': 'header'},
                'Authorization': {
                    'description': 'Bearer <jwt>', 
                    'in': 'header', 
                    'required': not Config.DEV_MODE
                },
                'user_id': {'description': '<사용자 UUID>', 'in': 'header', 'required': True}
            })
    @ns.response(201, '세션이 생성됨', session_response)
    @ns.response(400, '잘못된 요청')
    @ns.response(401, '인증 실패')
    @require_auth
    def post(self):
        """새로운 채팅 세션을 생성합니다."""
        user_id = request.headers.get('user_id')
        if not user_id:
            return {'error': 'user_id is required'}, 400

        try:
            session = session_service.create_session(uuid.UUID(user_id))
            return {"session_id": str(session.id)}
        except Exception as e:
            return {'error': str(e)}, 400


@ns.route('/<uuid:session_id>/close')
class SessionClose(Resource):
    @ns.doc('세션 닫기',
            description='채팅 세션을 종료하고 요약 정보를 생성합니다.',
            security='Bearer' if not Config.DEV_MODE else None,
            params={
                'Authorization': {
                    'description': 'Bearer <jwt>', 
                    'in': 'header', 
                    'required': not Config.DEV_MODE
                }
            })
    @ns.response(200, '세션이 종료됨', session_close_response)
    @ns.response(400, '잘못된 요청')
    @ns.response(401, '인증 실패')
    @require_auth
    def post(self, session_id):
        """채팅 세션을 종료하고 요약 정보를 생성합니다."""
        try:
            session = session_service.finish_session(session_id)
            return {
                'id': str(session.id),
                'user_id': str(session.user_id),
                'start_at': session.start_at,
                'finish_at': session.finish_at,
                'title': session.title,
                'description': session.description
            }
        except Exception as e:
            return {'error': str(e)}, 400


@ns.route('/<uuid:session_id>/send')
class MessageSend(Resource):
    @ns.doc('메시지 전송',
            description='사용자 메시지를 전송하고 AI의 응답을 스트리밍으로 받습니다.',
            security='Bearer' if not Config.DEV_MODE else None,
            params={
                'Authorization': {
                    'description': 'Bearer <jwt>', 
                    'in': 'header', 
                    'required': not Config.DEV_MODE
                },
                'user_id': {'description': '<사용자 UUID>', 'in': 'header', 'required': True}
            })
    @ns.expect(message_send_input)
    @ns.response(200, 'AI 응답 스트림')
    @ns.response(400, '잘못된 요청')
    @ns.response(401, '인증 실패')
    @ns.response(500, 'AI 응답 생성 실패')
    @require_auth
    def post(self, session_id):
        """사용자 메시지를 전송하고 AI의 응답을 스트리밍으로 받습니다."""
        try:
            user_id = request.headers.get('user_id')
            content = request.json.get('content')
            
            if not user_id or not content:
                return {'error': 'user_id and content are required'}, 400

            def generate():
                for chunk in message_service.create_langgraph_completion(
                    session_id=session_id,
                    user_id=user_id,
                    content=content
                ):
                    if isinstance(chunk, dict):
                        chunk = json.dumps(chunk)
                    yield f"data: {chunk}\n\n"

            return Response(
                stream_with_context(generate()),
                mimetype='text/event-stream',
                headers={
                    'Cache-Control': 'no-cache',
                    'Connection': 'keep-alive',
                    'Content-Type': 'text/event-stream'
                }
            )
        except ValueError as e:
            return {'error': str(e)}, 400
        except Exception as e:
            print("Error in message completion:", str(e))
            return {'error': str(e)}, 500


@ns.route('/<uuid:user_id>')
class UserSessions(Resource):
    @ns.doc('사용자 세션 목록',
            description='특정 사용자의 모든 채팅 세션 목록을 가져옵니다.',
            security='Bearer' if not Config.DEV_MODE else None,
            params={
                'Authorization': {
                    'description': 'Bearer <jwt>', 
                    'in': 'header', 
                    'required': not Config.DEV_MODE
                }
            })
    @ns.response(200, '세션 목록 조회 성공', [session_close_response])
    @ns.response(400, '잘못된 요청')
    @ns.response(401, '인증 실패')
    @require_auth
    def get(self, user_id):
        """특정 사용자의 모든 채팅 세션 목록을 가져옵니다."""
        try:
            return session_service.get_user_sessions(user_id)
        except Exception as e:
            return {'error': str(e)}, 400


@ns.route('/<uuid:session_id>/m')
class SessionMessages(Resource):
    @ns.doc('세션 메시지 목록',
            description='특정 세션의 모든 메시지 기록을 가져옵니다.',
            security='Bearer' if not Config.DEV_MODE else None,
            params={
                'Authorization': {
                    'description': 'Bearer <jwt>', 
                    'in': 'header', 
                    'required': not Config.DEV_MODE
                }
            })
    @ns.response(200, '메시지 목록 조회 성공', [session_message_response])
    @ns.response(400, '잘못된 요청')
    @ns.response(401, '인증 실패')
    @require_auth
    def get(self, session_id):
        """특정 세션의 모든 메시지 기록을 가져옵니다."""
        try:
            return message_service.get_session_messages(session_id)
        except Exception as e:
            return {'error': str(e)}, 400
