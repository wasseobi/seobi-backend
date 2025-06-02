from flask_restx import Namespace, Resource, fields
from app.services.schedule_service import ScheduleService
from app.utils.auth_middleware import require_auth

ns = Namespace('schedule', description='일정 관리 API')

schedule_model = ns.model('Schedule', {
    'id': fields.String,
    'user_id': fields.String,
    'title': fields.String,
    'repeat': fields.String,
    'start_at': fields.DateTime,
    'finish_at': fields.DateTime,
    'location': fields.String,
    'status': fields.String(enum=['undone', 'doing', 'done']),
    'memo': fields.String,
    'linked_service': fields.String,
})

create_schedule_model = ns.model('ScheduleCreate', {
    'user_id': fields.String(required=True),
    'title': fields.String(required=True),
    'repeat': fields.String,
    'start_at': fields.DateTime,
    'finish_at': fields.DateTime,
    'location': fields.String,
    'status': fields.String(enum=['undone', 'doing', 'done']),
    'memo': fields.String,
    'linked_service': fields.String(required=True),
})

service = ScheduleService()

@ns.route('/<uuid:user_id>')
class ScheduleList(Resource):
    @ns.marshal_list_with(schedule_model)
    @require_auth
    def get(self, user_id):
        """특정 사용자의 모든 일정 조회"""
        return service.get_user_schedules(user_id)

    @ns.expect(create_schedule_model)
    @ns.marshal_with(schedule_model)
    @require_auth
    def post(self, user_id):
        """새 일정 생성"""
        from flask import request
        data = request.json
        data['user_id'] = str(user_id)
        data.pop('id', None)  # 혹시라도 id가 들어오면 제거
        return service.create_schedule(data), 201

@ns.route('/detail/<uuid:schedule_id>')
class ScheduleDetail(Resource):
    @ns.marshal_with(schedule_model)
    @require_auth
    @ns.response(404, '일정이 존재하지 않음')
    def get(self, schedule_id):
        """일정 상세 조회"""
        schedule = service.get_schedule(schedule_id)
        if not schedule:
            ns.abort(404, "해당 일정이 존재하지 않습니다.")
        return schedule

    @require_auth
    def delete(self, schedule_id):
        """일정 삭제"""
        result = service.delete_schedule(schedule_id)
        if result:
            return {'result': 'deleted'}
        return {'error': 'not found'}, 404
