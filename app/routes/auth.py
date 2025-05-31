"""인증 관련 라우트를 정의하는 모듈입니다."""
from flask import request
from flask_restx import Resource, Namespace, fields
from flask_jwt_extended import create_access_token, jwt_required
import google.auth.transport.requests
import google.oauth2.id_token
from app.models.db import db
from app.models.user import User
from app.services.user_service import UserService
from app.utils.app_config import get_auth_config, is_dev_mode

# Create namespace
ns = Namespace('auth', description='사용자 인증 작업')

# Define request/response models
sign_input = ns.model('GoogleSignIn', {
    'id_token': fields.String(required=True, 
                            description='구글에서 받은 ID 토큰',
                            example='eyJhbGciOiJSUzI1NiIsImtpZCI6IjFiZDY3...')
})

sign_response = ns.model('SignInResponse', {
    'access_token': fields.String(description='생성된 JWT 토큰',
                                example='jwt-token')
})

verify_response = ns.model('VerifyResponse', {
    'valid': fields.Boolean(description='토큰 유효성 여부',
                          example=True)
})

@ns.route('/sign')
class SignIn(Resource):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.user_service = UserService()

    @ns.doc('구글 로그인',
            description='구글 ID 토큰으로 로그인하고 JWT 토큰을 발급받습니다.',
            params={'Content-Type': {'description': 'application/json', 'in': 'header'}})
    @ns.expect(sign_input)
    @ns.response(200, '로그인 성공', sign_response)
    @ns.response(400, '잘못된 요청')
    @ns.response(401, '인증 실패')
    def post(self):
        """구글 ID 토큰으로 로그인하고 JWT 토큰을 발급받습니다."""
        id_token = request.json.get('id_token')
        if not id_token:
            return {'error': 'id_token required'}, 400
            
        try:
            # Verify Google token
            request_adapter = google.auth.transport.requests.Request()
            id_info = google.oauth2.id_token.verify_oauth2_token(
                id_token, request_adapter, get_auth_config()['google_client_id'])
            
            # Get user info
            email = id_info.get('email')
            username = id_info.get('name') or (email.split('@')[0] if email else None)
            
            if not email:
                return {'error': 'No email in token'}, 400

            # Find or create user
            user = self.user_service.get_user_by_email(email)
            if not user:
                user = self.user_service.create_user(username=username, email=email)

            # Create JWT token
            access_token = create_access_token(identity=user['id'])
            
            return {'access_token': access_token}

        except Exception as e:
            return {'error': 'Invalid id_token', 'detail': str(e)}, 401

@ns.route('/verify')
class TokenVerify(Resource):
    @ns.doc('토큰 검증',
            description='JWT 토큰의 유효성을 검증합니다.',
            security='Bearer' if not is_dev_mode() else None,
            params={
                'Content-Type': {'description': 'application/json', 'in': 'header'},
                'Authorization': {
                    'description': 'Bearer <jwt>', 
                    'in': 'header', 
                    'required': not is_dev_mode()
                }
            })
    @ns.response(200, '토큰 검증 성공', verify_response)
    @ns.response(401, '인증 실패')
    @jwt_required()
    def get(self):
        """JWT 토큰의 유효성을 검증합니다."""
        return {'valid': True}
