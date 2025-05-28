"""세션 관련 라우트를 정의하는 모듈입니다."""
from flask import request, Response, stream_with_context
from flask_restx import Resource, Namespace, fields
from app.services.session_service import SessionService
from app.services.message_service import MessageService
from app.services.interest_service import InterestService
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
    'user-id': fields.String(description='사용자 UUID',
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
    'user-id': fields.String(description='사용자 UUID',
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
interest_service = InterestService()


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
                'user-id': {'description': '<사용자 UUID>', 'in': 'header', 'required': True}
            })
    @ns.response(201, '세션이 생성됨', session_response)
    @ns.response(400, '잘못된 요청')
    @ns.response(401, '인증 실패')
    @require_auth
    def post(self):
        """새로운 채팅 세션을 생성합니다."""
        import logging
        logger = logging.getLogger(__name__)
        logger.debug(f"[헤더 확인] request.headers: {dict(request.headers)}")

        user_id = (
            request.headers.get('user-id')
            or request.headers.get('User-Id')
        )
        if not user_id:
            return {'error': 'user-id is required'}, 400

        try:
            session = session_service.create_session(uuid.UUID(user_id))
            return {"session_id": str(session["id"])}, 201
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
            # 1-1. 전체 메시지 기반 요약 생성
            session_service.summarize_session(session_id)

            # 1-2. 관심사 추출
            interest_service.extract_interests_keywords(session_id)
            
            # 2. finish_at 저장
            session = session_service.finish_session(session_id)
            return {
                'id': str(session["id"]),
                'user_id': str(session["user_id"]),
                'start_at': session["start_at"],
                'finish_at': session["finish_at"],
                'title': session["title"],
                'description': session["description"]
            }
        except Exception as e:
            ns.abort(400, f"Failed to close session: {str(e)}")


@ns.route('/<uuid:session_id>/send')
@ns.param('session_id', 'The session identifier')
@ns.response(404, 'Session not found')
@ns.response(400, 'Invalid input or session is finished')
@ns.response(500, 'Failed to get AI completion')
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
                'Accept': {
                    'description': 'text/event-stream',
                    'in': 'header',
                    'required': True
                },
                'user-id': {'description': '<사용자 UUID>', 'in': 'header', 'required': True}
            })
    @ns.expect(message_send_input)
    @require_auth
    def post(self, session_id):
        """Create a completion using LangGraph"""
        try:
            user_id = request.headers.get('user-id')
            if not user_id:
                ns.abort(400, "User ID is required")

            data = request.get_json()
            if not data or 'content' not in data:
                ns.abort(400, "Message content is required")

            user_message = data['content']
            assistant_message_chunks = []

            def generate():
                try:
                    for chunk in message_service.create_langgraph_completion(
                        session_id=session_id,
                        user_id=uuid.UUID(user_id),
                        content=user_message
                    ):
                        if 'content' in chunk:
                            assistant_message_chunks.append(chunk['content'])
                        yield f"data: {json.dumps(chunk, ensure_ascii=False)}\n\n"
                except Exception as e:
                    yield f"data: {json.dumps({'type': 'error', 'error': str(e)}, ensure_ascii=False)}\n\n"
                finally:
                    try:
                        messages = message_service.get_session_messages(
                            session_id)
                        user_count = sum(
                            1 for m in messages if m.get('role') == 'user')
                        assistant_count = sum(
                            1 for m in messages if m.get('role') == 'assistant')
                        if user_count == 1 and assistant_count >= 1:
                            user_msg = next((m['content'] for m in messages if m.get(
                                'role') == 'user'), user_message)
                            assistant_msg = next(
                                (
                                    m['content']
                                    for m in messages
                                    if m.get('role') == 'assistant'
                                    and m.get('metadata')
                                    and 'tools_used' in m.get('metadata')
                                    and m.get('content')
                                ),
                                None
                            )
                            if not assistant_msg:
                                assistant_msg = next((m['content'] for m in messages if m.get(
                                    'role') == 'assistant' and m.get('content')), '')
                            session_service.update_summary_conversation(
                                session_id,
                                user_msg,
                                assistant_msg
                            )
                    except Exception:
                        pass
                    yield "data: [DONE]\n\n"

            return Response(
                stream_with_context(generate()),
                mimetype='text/event-stream',
                headers={
                    'Cache-Control': 'no-cache',
                    'Connection': 'keep-alive',
                    'X-Accel-Buffering': 'no'
                }
            )

        except ValueError as e:
            ns.abort(400, str(e))
        except Exception as e:
            ns.abort(500, str(e))


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
            sessions = session_service.get_user_sessions(user_id)
            return [{
                'id': str(session.id),
                'user_id': str(session.user_id),
                'start_at': session.start_at,
                'finish_at': session.finish_at,
                'title': session.title,
                'description': session.description
            } for session in sessions]
        except Exception as e:
            ns.abort(400, f"Failed to get user sessions: {str(e)}")


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
            messages = message_service.get_session_messages(session_id)
            return messages
        except Exception as e:
            ns.abort(400, f"Failed to get session messages: {str(e)}")
