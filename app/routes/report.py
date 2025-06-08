"""리포트 기록 관련 라우트를 정의하는 모듈입니다."""
from flask import request
from flask_restx import Resource, Namespace, fields
from app.services.reports.report_service import ReportService
from app.utils.auth_middleware import require_auth
from app.utils.app_config import is_dev_mode
from app.services.briefing_service import BriefingService
from app import api
import uuid
import json

# Create namespace
ns = Namespace('report', description='레포트 작성 및 조회')

# Define models for documentation
report_response = ns.model('ReportResponse', {
    'id': fields.String(description='리포트 ID', example=str(uuid.uuid4())),
    'user_id': fields.String(description='사용자 ID', example=str(uuid.uuid4())),
    'content': fields.Raw(description='리포트 내용 (JSON 형식)',
                          example={"text": "오늘의 업무 요약", "script": "오늘의 업무 스크립트"}),
    'type': fields.String(enum=['daily', 'weekly', 'monthly'], description='리포트 유형', example='daily'),
})

report_content_response = ns.model('ReportContentResponse', {
    'text': fields.String(description='리포트 요약'),
    'script': fields.String(description='리포트 스크립트')
})

service = ReportService()
briefing_service = BriefingService()


@ns.route('/<uuid:user_id>')
class ReportList(Resource):
    @ns.marshal_list_with(report_response)
    @ns.doc('사용자 리포트 목록',
            description='특정 사용자의 모든 리포트 목록을 가져옵니다.',
            security='Bearer' if not is_dev_mode() else None,
            params={
                'Authorization': {
                    'description': 'Bearer <jwt>',
                    'in': 'header',
                    'required': not is_dev_mode()
                },
                'user-id': {'description': '<사용자 UUID>', 'in': 'header', 'required': True}
            })
    @require_auth
    def get(self, user_id):
        """특정 사용자의 모든 리포트 조회"""
        header_user_id = (
            request.headers.get('user-id')
            or request.headers.get('User-Id')
        )
        if not header_user_id:
            return {"message": "user-id header is required"}, 400
            
        if str(user_id) != str(header_user_id):
            return {"message": "Path user_id does not match header user_id"}, 400
            
        return service.get_user_reports(user_id)


@ns.route('/report/d')
class DailyReport(Resource):
    @ns.marshal_list_with(report_response)
    @ns.doc('데일리 리포트 조회',
            description='특정 사용자의 데일리 리포트를 조회합니다.',
            security='Bearer' if not is_dev_mode() else None,
            params={
                'Authorization': {
                    'description': 'Bearer <jwt>',
                    'in': 'header',
                    'required': not is_dev_mode()
                },
                'user-id': {'description': '<사용자 UUID>', 'in': 'header', 'required': True}
            })
    @require_auth
    def get(self):
        """특정 사용자의 데일리 리포트 조회"""
        user_id = (
            request.headers.get('user-id')
            or request.headers.get('User-Id')
        )
        if not user_id:
            return {"message": "user-id header is required"}, 400
            
        return service.get_user_type_reports(user_id, 'daily')

    @ns.marshal_with(report_content_response)
    @ns.doc('데일리 리포트 생성',
            description='데일리 리포트를 생성합니다. ',
            security='Bearer' if not is_dev_mode() else None,
            params={
                'Content-Type': {'description': 'application/json', 'in': 'header'},
                'Authorization': {
                    'description': 'Bearer <jwt>',
                    'in': 'header',
                    'required': not is_dev_mode()
                },
                'user-id': {'description': '<사용자 UUID>', 'in': 'header', 'required': True},
                'timezone': {'description': '타임존 (예: Asia/Seoul)', 'in': 'header', 'default': 'Asia/Seoul'}
            })
    @require_auth
    def post(self):
        """새 데일리 리포트 생성 (자동 생성)"""
        user_id = (
            request.headers.get('user-id')
            or request.headers.get('User-Id')
        )
        tz_str = request.headers.get('timezone', 'Asia/Seoul')

        if not user_id:
            return {"message": "user-id header is required"}, 400

        # 1. 리포트 내용 생성
        content = service.generate_report(
            user_id=user_id,
            tz_str=tz_str,
            report_type='daily'
        )

        briefing_service.create_briefing(
            user_id=user_id,
            content=content['text'],
            script=content['script']
        )

        # 2. 생성된 리포트를 DB에 저장
        service.save_report(
            user_id=user_id,
            content=content,
            report_type='daily'
        )

        return content, 201


@ns.route('/report/w')
class WeeklyReport(Resource):
    @ns.marshal_list_with(report_response)
    @ns.doc('위클리 리포트 조회',
            description='특정 사용자의 위클리 리포트를 조회합니다.',
            security='Bearer' if not is_dev_mode() else None,
            params={
                'Authorization': {
                    'description': 'Bearer <jwt>',
                    'in': 'header',
                    'required': not is_dev_mode()
                },
                'user-id': {'description': '<사용자 UUID>', 'in': 'header', 'required': True}
            })
    @require_auth
    def get(self):
        """특정 사용자의 위클리 리포트 조회"""
        user_id = (
            request.headers.get('user-id')
            or request.headers.get('User-Id')
        )
        if not user_id:
            return {"message": "user-id header is required"}, 400
            
        return service.get_user_type_reports(user_id, 'weekly')

    @ns.marshal_with(report_content_response)
    @ns.doc('위클리 리포트 생성',
            description='위클리 리포트를 생성합니다. ',
            security='Bearer' if not is_dev_mode() else None,
            params={
                'Content-Type': {'description': 'application/json', 'in': 'header'},
                'Authorization': {
                    'description': 'Bearer <jwt>',
                    'in': 'header',
                    'required': not is_dev_mode()
                },
                'user-id': {'description': '<사용자 UUID>', 'in': 'header', 'required': True},
                'timezone': {'description': '타임존 (예: Asia/Seoul)', 'in': 'header', 'default': 'Asia/Seoul'}
            })
    @require_auth
    def post(self):
        """새 위클리 리포트 생성 (자동 생성)"""
        user_id = (
            request.headers.get('user-id')
            or request.headers.get('User-Id')
        )
        tz_str = request.headers.get('timezone', 'Asia/Seoul')

        if not user_id:
            return {"message": "user-id header is required"}, 400

        # 1. 리포트 내용 생성
        content = service.generate_report(
            user_id=user_id,
            tz_str=tz_str,
            report_type='weekly'
        )

        # 2. 생성된 리포트를 DB에 저장
        service.save_report(
            user_id=user_id,
            content=content,
            report_type='weekly'
        )

        return content, 201

# @ns.route('/report/m')
# class MonthlyReport(Resource):
#     @ns.marshal_list_with(report_response)
#     @require_auth
#     def get(self, user_id):
#         """특정 사용자의 먼슬리 리포트 조회"""
#         return service.get_user_type_reports(user_id, 'monthly')

#     @ns.expect(create_report_model)
#     @ns.marshal_with(report_response)
#     @require_auth
#     def post(self, user_id):
#         """새 먼슬리 리포트 생성 (자동 생성)"""
#         from flask import request
#         data = request.json
#         data['user_id'] = str(user_id)

#         # schedule_id, type, tz_str 등 필수값 추출
#         schedule_id = data['schedule_id']
#         report_type = 'monthly'
#         tz_str = data.get('tz_str', 'Asia/Seoul')   # 필요시 프론트에서 전달

#         return service.generate_and_create_report(
#             user_id=user_id,
#             schedule_id=schedule_id,
#             tz_str=tz_str,
#             report_type=report_type
#         ), 201
