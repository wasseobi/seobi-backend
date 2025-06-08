from flask_restx import Namespace, Resource, fields
from app.services.reports.report_service import ReportService
from app.utils.auth_middleware import require_auth

ns = Namespace('debug/report', description='리포트 API')

report_model = ns.model('Report', {
    'id': fields.String,
    'user_id': fields.String,
    'schedule_id': fields.String,
    'content': fields.Raw,  # content는 JSON/dict이므로 Raw로 변경
    'type': fields.String(enum=['daily', 'weekly', 'monthly']),
})

create_report_model = ns.model('ReportCreate', {
    'user_id': fields.String(required=True),
    'schedule_id': fields.String(required=True),
    # 'content': fields.String,
    'type': fields.String(enum=['daily', 'weekly', 'monthly'], required=True),
})

service = ReportService()

@ns.route('/<uuid:user_id>')
class ReportList(Resource):
    @ns.marshal_list_with(report_model)
    @require_auth
    def get(self, user_id):
        """특정 사용자의 모든 리포트 조회"""
        return service.get_user_reports(user_id)

    @ns.expect(create_report_model)
    @ns.marshal_with(report_model)
    @require_auth
    def post(self, user_id):
        """새 리포트 생성 (자동 생성)"""
        from flask import request
        data = request.json
        data['user_id'] = str(user_id)
        # schedule_id, type, tz_str 등 필수값 추출
        schedule_id = data['schedule_id']
        report_type = data.get('type', 'daily')
        tz_str = data.get('tz_str', 'Asia/Seoul')   # 필요시 프론트에서 전달
        return service.create_report(
            user_id=user_id,
            schedule_id=schedule_id,
            tz_str=tz_str,
            report_type=report_type
        ), 201

@ns.route('/detail/<uuid:report_id>')
class ReportDetail(Resource):
    @ns.marshal_with(report_model)
    @require_auth
    @ns.response(404, '리포트가 존재하지 않음')
    def get(self, report_id):
        """리포트 상세 조회"""
        report = service.get_report(report_id)
        if not report:
            ns.abort(404, "해당 리포트가 존재하지 않습니다.")
        return report

    @require_auth
    def delete(self, report_id):
        """리포트 삭제"""
        result = service.delete_report(report_id)
        if result:
            return {'result': 'deleted'}
        return {'error': 'not found'}, 404
