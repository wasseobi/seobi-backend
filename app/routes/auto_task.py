"""자동 업무 관련 라우트를 정의하는 모듈입니다."""
from flask_restx import Namespace, Resource
from flask import request
from app.services.auto_task_service import AutoTaskService
from app.schemas.auto_task_schema import register_models
from app.utils.auth_middleware import require_auth
from app import api

ns = Namespace('autotask', description='자동 업무 조회')

auto_task_model, create_auto_task_model, auto_task_response = register_models(ns)
auto_task_service = AutoTaskService()

@ns.route('/<uuid:user_id>/inactive')
@ns.param('user_id', '사용자 UUID')
class UserInactiveAutoTask(Resource):
    @ns.doc(
        'get_user_inactive_auto_tasks',
        description='사용자의 비활성화된 AI 자동 업무 목록을 조회합니다.',
        responses={
            200: '성공적으로 조회됨',
            404: '해당 사용자의 비활성화된 AI 자동 업무 없음',
            401: '인증 필요',
        }
    )
    @ns.marshal_list_with(auto_task_response)
    @require_auth
    def get(self, user_id):
        """사용자의 비활성화된 AI 자동 업무 목록을 조회합니다."""
        try:
            return auto_task_service.get_user_auto_tasks_by_active_option(user_id, active=False)
        except ValueError as e:
            ns.abort(404, str(e))
    
@ns.route('/<uuid:user_id>/active')
@ns.param('user_id', '사용자 UUID')
class UserActiveAutoTask(Resource):
    @ns.doc(
        'get_user_active_auto_tasks',
        description='사용자의 활성화된 AI 자동 업무 목록을 조회합니다.',
        responses={
            200: '성공적으로 조회됨',
            404: '해당 사용자의 활성화된 AI 자동 업무 없음',
            401: '인증 필요',
        }
    )
    @ns.marshal_list_with(auto_task_response)
    @require_auth
    def get(self, user_id):
        """사용자의 활성화된 AI 자동 업무 목록을 조회합니다."""
        try:
            return auto_task_service.get_user_auto_tasks_by_active_option(user_id, active=True)
        except ValueError as e:
            ns.abort(404, str(e))

@ns.route('/<uuid:auto_task_id>/active')
@ns.param('auto_task_id', '자동 업무(AutoTask) UUID')
@ns.param('active', '활성화 여부(True/False)', default=True)
class AutoTaskUpdateActive(Resource):
    @ns.doc(
        'update_status',
        description='auto_task_id에 해당하는 자동 업무(AutoTask)의 active(True/False)를 업데이트합니다.',
        responses={
            200: '업데이트 성공',
            404: '해당 AutoTask 없음',
            400: '입력값 오류',
            401: '인증 필요',
        }
    )
    @ns.param('active', '활성화 여부(True/False)', default=True)
    @ns.marshal_with(auto_task_model)
    @require_auth
    def put(self, auto_task_id):
        """
        auto_task_id에 해당하는 자동 업무(AutoTask)의 active(True/False)를 업데이트합니다.
        """
        active = request.args.get('active')
        try:
            return auto_task_service.update_active(auto_task_id, active=active)
        except ValueError as e:
            ns.abort(404, str(e))

# Register the namespace
api.add_namespace(ns) 