"""메시지 기록 관련 라우트를 정의하는 모듈입니다."""
from flask import request, current_app
from flask_restx import Resource, Namespace, fields
from app.services.message_service import MessageService
from app.utils.auth_middleware import require_auth
from app import api
import uuid
import json

# Create namespace
ns = Namespace('m', description='메시지 기록 조회')

# Define models for documentation
message_response = ns.model('MessageResponse', {
    'id': fields.String(description='메시지 UUID',
                       example='123e4567-e89b-12d3-a456-426614174000'),
    'session_id': fields.String(description='세션 UUID',
                              example='321e1267-e89b-12d3-a456-23131232330'),
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

# Initialize service
message_service = MessageService()

@ns.route('/<uuid:user_id>')
class UserMessages(Resource):
    @ns.doc('사용자 전체 메시지',
            description='특정 사용자의 모든 메시지 기록을 가져옵니다.',
            security='Bearer' if not current_app.config['DEV_MODE'] else None,
            params={
                'Authorization': {
                    'description': 'Bearer <jwt>', 
                    'in': 'header', 
                    'required': not current_app.config['DEV_MODE']
                }
            })
    @ns.response(200, '메시지 목록 조회 성공', [message_response])
    @ns.response(400, '잘못된 요청')
    @ns.response(401, '인증 실패')
    @require_auth
    def get(self, user_id):
        """특정 사용자의 모든 메시지 기록을 가져옵니다."""
        try:
            return message_service.get_user_messages(user_id)
        except Exception as e:
            return {'error': str(e)}, 400
