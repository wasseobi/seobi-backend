"""인증 미들웨어 모듈입니다."""
import os
import jwt
import logging
from functools import wraps
from flask import request, jsonify
from config import Config

# 로깅 설정
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def require_auth(f):
    """인증이 필요한 엔드포인트에 적용할 데코레이터입니다."""
    @wraps(f)
    def decorated(*args, **kwargs):
        # 개발 모드 체크
        if Config.DEV_MODE:
            logger.info(f"[DEV_MODE] Endpoint accessed: {request.path}")
            return f(*args, **kwargs)

        # 토큰 확인
        auth_header = request.headers.get('Authorization')
        if not auth_header:
            return jsonify({'message': '인증 토큰이 필요합니다.'}), 401

        try:
            # Bearer 토큰에서 실제 토큰 부분만 추출
            token = auth_header.split(' ')[1]
            # 토큰 검증
            payload = jwt.decode(
                token, 
                Config.JWT_SECRET_KEY,
                algorithms=['HS256']
            )
            
            # 사용자 ID를 request에 저장
            request.user_id = payload.get('sub')
            
            # 접근 로깅
            logger.info(f"User {request.user_id} accessed: {request.path}")
            
            return f(*args, **kwargs)
            
        except jwt.ExpiredSignatureError:
            return jsonify({'message': '만료된 토큰입니다.'}), 401
        except jwt.InvalidTokenError:
            return jsonify({'message': '유효하지 않은 토큰입니다.'}), 401
        
    return decorated
