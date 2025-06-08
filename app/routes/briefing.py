from flask_restx import Resource, Namespace

from app import api
from app.services.briefing_service import BriefingService
from app.schemas.briefing_schema import register_models
from app.utils.auth_middleware import require_auth

ns = Namespace('briefing', description='브리핑 조회')

briefing_create, briefing_update, briefing_response = register_models(ns)

briefing_service = BriefingService()

@ns.route('/<uuid:user_id>')
@ns.param('user_id', 'The user identifier')
@ns.response(404, 'User not found')
class UserBriefing(Resource):
    @ns.doc('get_user_briefing')
    @ns.marshal_list_with(briefing_response)
    @require_auth
    def get(self, user_id):
        """특정 사용자의 오늘 브리핑 조회"""
        try:
            briefing = briefing_service.get_user_today_briefing(user_id)
            briefing_service.update_briefing(briefing['id'])

            return briefing_service.get_user_today_briefing(user_id)
        except ValueError as e:
            ns.abort(404, str(e))
        except Exception as e:
            ns.abort(500, str(e))

# Register the namespace
api.add_namespace(ns) 