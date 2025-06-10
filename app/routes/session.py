"""세션 관련 라우트를 정의하는 모듈입니다."""
from flask import request, Response, stream_with_context
from flask_restx import Resource, Namespace, fields
from app.services.cleanup_service import CleanupService
from app.services.session_service import SessionService
from app.services.message_service import MessageService
from app.services.interest_service import InterestService
from app.services.user_service import UserService
from app.services.background_service import BackgroundService
from app.services.auto_task_service import AutoTaskService
from app.utils.auth_middleware import require_auth
from app.utils.agent_state_store import AgentStateStore
from app.utils.auto_task_utils import safe_background_response
from app.utils.app_config import is_dev_mode
from app.utils.prompt.service_prompts import (
    SESSION_SUMMARY_SYSTEM_PROMPT,
    SESSION_SUMMARY_USER_PROMPT
)
import uuid
import json
import logging
import time
from datetime import datetime
import threading

# cleanup 로거 설정
log = logging.getLogger("langgraph_debug")

# Create namespace
ns = Namespace('s', description='채팅 세션 및 메시지 작업')

# Define models for documentation
session_open_input = ns.model('SessionOpenInput', {
    'user_location': fields.String(required=False,
                                   description='사용자의 위치 정보 (선택사항)',
                                   example='서울')
})

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
user_service = UserService()
cleanup_service = CleanupService()
auto_task_service = AutoTaskService()
background_service = BackgroundService()


@ns.route('/open')
class SessionOpen(Resource):
    @ns.doc('세션 열기',
            description='새로운 채팅 세션을 생성합니다.',
            security='Bearer' if not is_dev_mode() else None,
            params={
                'Content-Type': {'description': 'application/json', 'in': 'header'},
                'Authorization': {
                    'description': 'Bearer <jwt>',
                    'in': 'header',
                    'required': not is_dev_mode()
                },
                'user-id': {'description': '<사용자 UUID>', 'in': 'header', 'required': True}
            })
    @ns.expect(session_open_input)
    @ns.response(201, '세션이 생성됨', session_response)
    @ns.response(400, '잘못된 요청')
    @ns.response(401, '인증 실패')
    @require_auth
    def post(self):
        """새로운 채팅 세션을 생성합니다."""
        user_id = (
            request.headers.get('user-id')
            or request.headers.get('User-Id')
        )
        if not user_id:
            return {'error': 'user-id is required'}, 400

        try:
            session = session_service.create_session(uuid.UUID(user_id))
            agent_state = user_service.initialize_agent_state(user_id)
            data = request.get_json() or {}
            if 'user_location' in data:
                agent_state['user_location'] = data['user_location']
            else:
                agent_state['user_location'] = None

            AgentStateStore.set(user_id, agent_state)
            return {"session_id": str(session["id"])}, 201
        except Exception as e:
            return {'error': str(e)}, 400


@ns.route('/<uuid:session_id>/close')
class SessionClose(Resource):
    @ns.doc('세션 닫기',
            description='채팅 세션을 종료하고 요약 정보를 생성합니다.',
            security='Bearer' if not is_dev_mode() else None,
            params={
                'Authorization': {
                    'description': 'Bearer <jwt>',
                    'in': 'header',
                    'required': not is_dev_mode()
                }
            })
    @ns.response(200, '세션이 종료됨', session_close_response)
    @ns.response(400, '잘못된 요청')
    @ns.response(401, '인증 실패')
    @require_auth
    def post(self, session_id):
        """채팅 세션을 종료하고 요약 정보를 생성합니다."""
        errors = []
        session = None

        try:
            # NOTE(GideokKim): session을 닫을 때 많은 작업을 수행하지만 DB에 session을 반드시 닫아야 하므로 가장 앞에 위치함
            try:
                session = session_service.finish_session(session_id)
            except Exception as e:
                error_msg = f"Failed to finish session: {str(e)}"
                log.error(error_msg)
                errors.append({"step": "session_finish", "error": error_msg})

            # 1-1. 전체 메시지 기반 요약 생성
            try:
                messages = message_service.get_session_messages(session_id)
                # NOTE(GideokKim): 메시지 중 assistant 메시지는 제외하고 요약하도록 변경함.
                #                  간헐적으로 assistant 메시지가 포함되면 OpenAI 정책을 위반하는 케이스가 발생함.
                # TODO(GideokKim): 나중에 정책 위반 방지를 위한 필터 기능을 구현하고 assistant 메시지도 포함하도록 구현해야 함.
                dialogue = "\n".join(
                    f"{m['role']}: {m['content']}" for m in messages if m['role'] in 'user' and m.get('content')
                )
                context_messages = [
                    {"role": "system", "content": SESSION_SUMMARY_SYSTEM_PROMPT},
                    {"role": "user", "content": dialogue}
                ]
                session = session_service.update_session_summary(
                    session_id, context_messages)
            except Exception as e:
                error_msg = f"Failed to generate session summary: {str(e)}"
                log.error(error_msg)
                errors.append(
                    {"step": "summary_generation", "error": error_msg})

            # 1-2. 관심사 추출
            log.info(f"[{datetime.now()}] 관심사 추출 시작")

            def run_interest_extraction():
                try:
                    log.info(f"[{datetime.now()}] 관심사 추출 백그라운드 스레드 시작")
                    start_time = time.time()
                    from app import create_app
                    app = create_app()
                    with app.app_context():
                        interest_service.extract_interests_keywords(session_id)
                    end_time = time.time()
                    log.info(f"[{datetime.now()}] 관심사 추출 백그라운드 완료 - 소요시간: {end_time - start_time:.2f}초")
                except Exception as e:
                    error_msg = f"Failed to extract interests: {str(e)}"
                    log.error(error_msg)
                    errors.append(
                        {"step": "interest_extraction", "error": error_msg})
                
            interest_thread = threading.Thread(target=run_interest_extraction)
            interest_thread.daemon = True
            interest_thread.start()
            
            log.info(f"[{datetime.now()}] 관심사 추출 백그라운드 시작됨 - API 응답 즉시 반환")

            user_id = str(session["user_id"])

            # 1-3. 세션 cleanup 실행
            log.info(f"[{datetime.now()}] Cleanup 시작")

            def run_cleanup():
                try:
                    log.info(f"[{datetime.now()}] Cleanup 백그라운드 스레드 시작")
                    start_time = time.time()
                    
                    from app import create_app
                    app = create_app()
                    with app.app_context():
                        cleanup_result = cleanup_service.cleanup_session(session_id)
                    
                    end_time = time.time()
                    log.info(f"[{datetime.now()}] Cleanup 백그라운드 완료 - 소요시간: {end_time - start_time:.2f}초")
                    
                    # cleanup 완료 후 auto task 생성도 백그라운드에서 실행
                    if cleanup_result and not cleanup_result.get("error") and cleanup_result.get("generated_tasks"):
                        run_auto_task_creation(cleanup_result)
                        run_background_auto_task(user_id)
                        
                except Exception as e:
                    log.error(f"[{datetime.now()}] Cleanup 백그라운드 에러: {str(e)}")

            def run_auto_task_creation(cleanup_result):
                try:
                    log.info(f"[{datetime.now()}] Auto task 백그라운드 스레드 시작")
                    start_time = time.time()
                    
                    from app import create_app
                    app = create_app()
                    with app.app_context():
                        session = session_service.get_session(session_id)
                        if session:
                            auto_task_service.create_from_cleanup_result(
                                session["user_id"],
                                cleanup_result
                            )
                    
                    end_time = time.time()
                    log.info(f"[{datetime.now()}] Auto task 백그라운드 완료 - 소요시간: {end_time - start_time:.2f}초")
                except Exception as e:
                    log.error(f"[{datetime.now()}] Auto task 백그라운드 에러: {str(e)}")

                        # 1.4 백그라운드 자동 업무 실행
            def run_background_auto_task(user_id):
                try:
                    log.info(f"[{datetime.now()}] Background Auto task 백그라운드 스레드 시작")
                    start_time = time.time()
                    
                    from app import create_app
                    app = create_app()
                    with app.app_context():
                        background_result = background_service.background_auto_task(str(user_id))
                        background_result = safe_background_response(background_result)
                        print("[DEBUG] background_result:", background_result)
                        log.info(f"[{datetime.now()}] Background auto task 결과: {background_result}")

                    end_time = time.time()
                    log.info(f"[{datetime.now()}] Background auto task 백그라운드 완료 - 소요시간: {end_time - start_time:.2f}초")
                except Exception as e:
                    log.error(f"[{datetime.now()}] Background auto task 백그라운드 에러: {str(e)}")

            # 백그라운드에서 cleanup 실행 (join 없이)
            cleanup_thread = threading.Thread(target=run_cleanup)
            cleanup_thread.daemon = True  # 메인 프로세스 종료 시 함께 종료
            cleanup_thread.start()

            log.info(f"[{datetime.now()}] Cleanup 백그라운드 시작됨 - API 응답 즉시 반환")

            # 세션 종료 시 AgentState에서 user_memory 업데이트
            def run_user_memory_update():
                try:
                    log.info(f"[{datetime.now()}] User memory 업데이트 백그라운드 스레드 시작")
                    start_time = time.time()
                    
                    from app import create_app
                    app = create_app()
                    with app.app_context():
                        agent_state = AgentStateStore.get(user_id)
                        if agent_state:
                            user_service.save_user_memory_from_state(user_id, agent_state)
                            AgentStateStore.delete(user_id)
                            log.info(f"[{datetime.now()}] User memory 업데이트 완료")
                        else:
                            log.warning(f"AgentState not found for user {user_id} during session close")
                    
                    end_time = time.time()
                    log.info(f"[{datetime.now()}] User memory 업데이트 백그라운드 완료 - 소요시간: {end_time - start_time:.2f}초")
                        
                except Exception as e:
                    log.error(f"[{datetime.now()}] User memory 업데이트 백그라운드 에러: {str(e)}")
            
            # 백그라운드에서 user memory 업데이트 실행 (join 없이)
            memory_thread = threading.Thread(target=run_user_memory_update)
            memory_thread.daemon = True
            memory_thread.start()
            
            log.info(f"[{datetime.now()}] User memory 업데이트 백그라운드 시작됨 - API 응답 즉시 반환")

            response = {
                'id': str(session["id"]),
                'user_id': str(session["user_id"]),
                'start_at': session["start_at"],
                'finish_at': session["finish_at"],
                'title': session["title"],
                'description': session["description"]
            }

            # 에러가 있더라도 세션이 정상적으로 종료되었다면 200 응답
            if errors:
                response['warnings'] = errors
                return response, 200
            return response, 200

        except Exception as e:
            error_msg = f"Failed to close session: {str(e)}"
            log.error(error_msg)
            if errors:
                errors.append({"step": "session_close", "error": error_msg})
                return {"errors": errors}, 400
            return {"error": error_msg}, 400


@ns.route('/<uuid:session_id>/send')
@ns.param('session_id', 'The session identifier')
@ns.response(404, 'Session not found')
@ns.response(400, 'Invalid input or session is finished')
@ns.response(500, 'Failed to get AI completion')
class MessageSend(Resource):
    @ns.doc('메시지 전송',
            description='사용자 메시지를 전송하고 AI의 응답을 스트리밍으로 받습니다.',
            security='Bearer' if not is_dev_mode() else None,
            params={
                'Authorization': {
                        'description': 'Bearer <jwt>',
                        'in': 'header',
                        'required': not is_dev_mode()
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
            security='Bearer' if not is_dev_mode() else None,
            params={
                'Authorization': {
                    'description': 'Bearer <jwt>',
                    'in': 'header',
                    'required': not is_dev_mode()
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
            return sessions
        except Exception as e:
            ns.abort(400, f"Failed to get user sessions: {str(e)}")


@ns.route('/<uuid:session_id>/m')
class SessionMessages(Resource):
    @ns.doc('세션 메시지 목록',
            description='특정 세션의 모든 메시지 기록을 가져옵니다.',
            security='Bearer' if not is_dev_mode() else None,
            params={
                'Authorization': {
                    'description': 'Bearer <jwt>',
                    'in': 'header',
                    'required': not is_dev_mode()
                }
            })
    @ns.response(200, '메시지 목록 조회 성공', [session_message_response])
    @ns.response(400, '잘못된 요청')
    @ns.response(401, '인증 실패')
    @require_auth
    def get(self, session_id):
        """특정 세션의 모든 메시지 기록을 가져옵니다."""
        try:
            messages = []
            for message in message_service.get_session_messages(session_id):
                message.pop('vector', None)
                messages.append(message)
            return messages, 200
        except Exception as e:
            print(e)
            ns.abort(400, f"Failed to get session messages: {str(e)}")
