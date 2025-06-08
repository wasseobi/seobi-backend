"""자동 업무 관련 라우트를 정의하는 모듈입니다."""
from flask_restx import Namespace, Resource
from flask import request
from datetime import datetime
from app.services.auto_task_service import AutoTaskService
from app.schemas.auto_task_schema import register_models
from app.utils.auth_middleware import require_auth
from app import api

ns = Namespace('debug/autotask', description='자동 업무 API')

auto_task_model, create_auto_task_model, auto_task_response = register_models(ns)
auto_task_service = AutoTaskService()

@ns.route('/')
class AutoTaskList(Resource):
    @ns.doc(
        'list_auto_task',
        description='모든 자동 업무(AutoTask) 목록을 최신 생성순으로 조회합니다.',
        responses={
            200: '성공적으로 조회됨',
            401: '인증 필요',
        }
    )
    @ns.marshal_list_with(auto_task_model)
    @require_auth
    def get(self):
        """
        모든 자동 업무(AutoTask) 목록을 최신 생성순으로 조회합니다.
        """
        return auto_task_service.get_all_auto_tasks()
    
@ns.route('/<uuid:auto_task_id>')
@ns.param('auto_task_id', '자동 업무(AutoTask) UUID')
class AutoTaskResource(Resource):
    @ns.doc(
        'get_auto_task',
        description='auto_task_id로 단일 자동 업무(AutoTask) 정보를 조회합니다.',
        responses={
            200: '성공적으로 조회됨',
            404: '해당 AutoTask 없음',
            401: '인증 필요',
        }
    )
    @ns.marshal_with(auto_task_model)
    @require_auth
    def get(self, auto_task_id):
        """
        auto_task_id로 단일 자동 업무(AutoTask) 정보를 조회합니다.
        """
        try:
            return auto_task_service.get_auto_task_by_id(auto_task_id)
        except ValueError as e:
            ns.abort(404, str(e))

    @ns.doc(
        'update_auto_task',
        description='auto_task_id에 해당하는 자동 업무(AutoTask) 정보를 수정합니다. 입력 필드는 일부만 전달해도 됩니다.',
        responses={
            200: '수정 성공',
            404: '해당 AutoTask 없음',
            400: '입력값 오류',
            401: '인증 필요',
        }
    )
    @ns.expect(create_auto_task_model)
    @ns.marshal_with(auto_task_model)
    @require_auth
    def put(self, auto_task_id):
        """
        auto_task_id에 해당하는 자동 업무(AutoTask) 정보를 수정합니다. 입력 필드는 일부만 전달해도 됩니다.
        """
        try:
            data = api.payload
            return auto_task_service.update(auto_task_id, **data)
        except ValueError as e:
            ns.abort(404, str(e))

    @ns.doc(
        'delete_auto_task',
        description='auto_task_id에 해당하는 자동 업무(AutoTask)를 삭제합니다.',
        responses={
            200: '삭제 성공',
            404: '해당 AutoTask 없음',
            401: '인증 필요',
        }
    )
    @require_auth
    def delete(self, auto_task_id):
        """
        auto_task_id에 해당하는 자동 업무(AutoTask)를 삭제합니다.
        """
        try:
            result = auto_task_service.delete(auto_task_id)
            return {'result': result}
        except ValueError as e:
            ns.abort(404, str(e))

@ns.route('/user/<uuid:user_id>')
@ns.param('user_id', '사용자(User) UUID')
class UserAutoTask(Resource):
    @ns.doc(
        'get_user_auto_task',
        description='특정 사용자의 모든 자동 업무(AutoTask) 목록을 조회합니다.',
        responses={
            200: '성공적으로 조회됨',
            404: '해당 사용자 없음',
            401: '인증 필요',
        }
    )
    @ns.marshal_list_with(auto_task_model)
    @require_auth
    def get(self, user_id):
        """
        특정 사용자의 모든 자동 업무(AutoTask) 목록을 조회합니다.
        """
        try:
            return auto_task_service.get_user_auto_tasks(user_id)
        except ValueError as e:
            ns.abort(404, str(e))

    @ns.doc(
        'create_auto_task',
        description='특정 사용자(user_id)에 대해 새로운 자동 업무(AutoTask)를 생성합니다.',
        responses={
            201: '생성 성공',
            400: '입력값 오류',
            401: '인증 필요',
        }
    )
    @ns.expect(create_auto_task_model)
    @ns.marshal_with(auto_task_model, code=201)
    @require_auth
    def post(self, user_id):
        """
        특정 사용자(user_id)에 대해 새로운 자동 업무(AutoTask)를 생성합니다.
        """
        try:
            data = api.payload
            return auto_task_service.create(user_id, **data), 201
        except ValueError as e:
            ns.abort(400, str(e))


@ns.route('/user/<uuid:user_id>/range')
@ns.param('user_id', '사용자(User) UUID')
@ns.param('start_at', '조회 시작일(YYYY-MM-DDTHH:MM:SS)', default='2025-06-01T00:00:00')
@ns.param('finish_at', '조회 종료일(YYYY-MM-DDTHH:MM:SS)', default='2025-06-01T23:59:59')
@ns.param('status', '상태(undone/done, None(전체))', default='undone')
class UserAutoTaskRange(Resource):
    @ns.doc(
        'get_all_by_user_id_in_range',
        description='특정 사용자의 기간 및 상태별 자동 업무(AutoTask) 목록을 조회합니다.',
        responses={
            200: '성공적으로 조회됨',
            404: '해당 기간에 업무 없음',
            401: '인증 필요',
        }
    )
    @ns.marshal_list_with(auto_task_model)
    @require_auth
    def get(self, user_id):
        """
        특정 사용자의 기간(start_at~finish_at) 및 상태(status)별 자동 업무(AutoTask) 목록을 조회합니다.
        """
        start = request.args.get('start_at')
        end = request.args.get('finish_at')
        status = request.args.get('status')
        if not start or not end:
            ns.abort(400, 'start_at, finish_at 쿼리 파라미터가 필요합니다.')
        try:
            start_at = datetime.fromisoformat(start)
            end_at = datetime.fromisoformat(end)
        except Exception:
            ns.abort(400, 'start_at, finish_at는 ISO8601 형식(YYYY-MM-DDTHH:MM:SS)이어야 합니다.')
        try:
            return auto_task_service.get_all_by_user_id_in_range(user_id, start_at, end_at, status)
        except ValueError as e:
            ns.abort(404, str(e))

@ns.route('/<uuid:auto_task_id>/finishTime')
@ns.param('auto_task_id', '자동 업무(AutoTask) UUID')
@ns.response(200, '업데이트 성공')
@ns.response(404, '해당 AutoTask 없음')
@ns.response(400, '입력값 오류')
@ns.response(401, '인증 필요')
class AutoTaskUpdateFinish(Resource):
    @ns.doc(
        'update_finish_time',
        description='auto_task_id에 해당하는 자동 업무(AutoTask)의 finish_at(완료 시각)을 업데이트합니다.'
    )
    @ns.param('finish_at', '완료 시각(YYYY-MM-DDTHH:MM:SS)', default='2025-06-01T00:00:00')
    @ns.marshal_with(auto_task_model)
    @require_auth
    def put(self, auto_task_id):
        """
        auto_task_id에 해당하는 자동 업무(AutoTask)의 finish_at(완료 시각)을 업데이트합니다.
        """
        finish_at = request.args.get('finish_at')
        if not finish_at:
            ns.abort(400, 'finish_at 쿼리 파라미터가 필요합니다.')
        try:
            finish_time = datetime.fromisoformat(finish_at)
        except Exception:
            ns.abort(400, 'finish_at는 ISO8601 형식(YYYY-MM-DDTHH:MM:SS)이어야 합니다.')
        try:
            return auto_task_service.update_finish_time(auto_task_id, finish_time)
        except ValueError as e:
            ns.abort(404, str(e))

@ns.route('/<uuid:auto_task_id>/status')
@ns.param('auto_task_id', '자동 업무(AutoTask) UUID')
@ns.response(200, '업데이트 성공')
@ns.response(404, '해당 AutoTask 없음')
@ns.response(400, '입력값 오류')
@ns.response(401, '인증 필요')
class AutoTaskUpdateStatus(Resource):
    @ns.doc(
        'update_status',
        description='auto_task_id에 해당하는 자동 업무(AutoTask)의 status(undone/done)를 업데이트합니다.',
    )
    @ns.param('status', '상태(undone/done)', default='undone')
    @ns.marshal_with(auto_task_model)
    @require_auth
    def put(self, auto_task_id):
        """
        auto_task_id에 해당하는 자동 업무(AutoTask)의 status(undone/done)를 업데이트합니다.
        """
        status = request.args.get('status')
        if not status:
            ns.abort(400, 'status 쿼리 파라미터가 필요합니다.')
        if status not in ['undone', 'done']:
            ns.abort(400, 'status는 undone 또는 done이어야 합니다.')
        try:
            return auto_task_service.update_status(auto_task_id, status)
        except ValueError as e:
            ns.abort(404, str(e))