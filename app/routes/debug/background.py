from flask_restx import Namespace, Resource
from app.services.background_service import BackgroundService
from app.schemas.background_schema import register_models
from app.utils.auth_middleware import require_auth
from app import api
import uuid

ns = Namespace('background', description='백그라운드 작업 실행')

background_model = register_models(ns)
background_service = BackgroundService()

def safe_background_response(data: dict) -> dict:
    result = {
        'user_id': data.get('user_id') or "",
        'finished': bool(data.get('finished'))
        }
    
    if data.get('task') is not None:
        result['task'] = data['task']
    if data.get('last_completed_title'):
        result['last_completed_title'] = data['last_completed_title']
    if data.get('error'):
        result['error'] = data['error']
    if data.get('step') is not None:
        result['step'] = data['step']
    return result
    
@ns.route('/auto-task/<uuid:user_id>')
@ns.param('user_id', '사용자(user) UUID')
class BackgroundAutoTask(Resource):
    @ns.doc(
        '백그라운드 오토테스크 실행',
        description='주어진 user_id로 백그라운드 오토테스크 워크플로우를 실행합니다.',
        responses={
            200: '실행 결과',
            400: '잘못된 요청',
            401: '인증 필요',
        }
    )
    @ns.marshal_with(background_model)
    @require_auth
    def post(self, user_id):
        """주어진 user_id로 백그라운드 오토테스크를 실행합니다."""
        try:
            result = background_service.background_auto_task(str(user_id))
            print("[DEBUG] before safe:", result)
            result = safe_background_response(result)
            print("[DEBUG] after safe:", result)
            if result.get("error") in ["No task to write", "모든 AutoTask 완료"]:
                # 모든 작업 정상 종료
                result["error"] = ""
                return result, 200
            elif "error" in result and result["error"]:
                return result, 400
            return result
        except Exception as e:
            return {'error': str(e)}, 400