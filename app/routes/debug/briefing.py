import uuid

from flask import request
from flask_restx import Resource, Namespace

from app import api
from app.services.briefing_service import BriefingService
from app.schemas.briefing_schema import register_models
from app.utils.auth_middleware import require_auth

ns = Namespace('debug/briefings', description='Briefing operations')

briefing_create, briefing_update, briefing_response = register_models(ns)

briefing_service = BriefingService()

@ns.route('/')
class BriefingList(Resource):
    @ns.doc('list_briefings')
    @ns.marshal_list_with(briefing_response)
    @require_auth
    def get(self):
        try:
            return briefing_service.get_all_briefings()
        except Exception as e:
            ns.abort(500, str(e))

    @ns.doc('create_briefing')
    @ns.expect(briefing_create)
    @ns.marshal_with(briefing_response, code=201)
    @ns.response(400, 'Invalid input')
    @ns.response(404, 'User not found')
    @require_auth
    def post(self):
        data = request.json

        if not data or 'user_id' not in data or 'content' not in data:
            ns.abort(400, 'user_id and content are required')
        try:
            briefing = briefing_service.create_briefing(
                user_id=uuid.UUID(data['user_id']),
                **{k: v for k, v in data.items() if k != 'user_id'}
            )
            return briefing, 201
        except Exception as e:
            ns.abort(500, str(e))

@ns.route('/<uuid:briefing_id>')
@ns.param('briefing_id', 'The briefing identifier')
@ns.response(404, 'Briefing not found')
class BriefingResource(Resource):
    @ns.doc('get_briefing')
    @ns.marshal_with(briefing_response)
    @require_auth
    def get(self, briefing_id):
        try:
            return briefing_service.get_briefing(briefing_id)
        except ValueError as e:
            ns.abort(404, str(e))
        except Exception as e:
            ns.abort(500, str(e))

    @ns.doc('update_briefing')
    @ns.expect(briefing_update)
    @ns.marshal_with(briefing_response)
    @ns.response(400, 'Invalid input')
    @require_auth
    def put(self, briefing_id):
        data = request.json

        if not data:
            ns.abort(400, 'No update data provided')
        try:
            return briefing_service.update_briefing(briefing_id, **data)
        except ValueError as e:
            ns.abort(404, str(e))
        except Exception as e:
            ns.abort(500, str(e))

    @ns.doc('delete_briefing')
    @ns.response(204, 'Briefing deleted')
    @require_auth
    def delete(self, briefing_id):
        try:
            briefing_service.delete_briefing(briefing_id)
            return '', 204
        except ValueError as e:
            ns.abort(404, str(e))
        except Exception as e:
            ns.abort(500, str(e))

@ns.route('/user/<uuid:user_id>')
@ns.param('user_id', 'The user identifier')
@ns.response(404, 'User not found')
class UserBriefings(Resource):
    @ns.doc('get_user_briefings')
    @ns.marshal_list_with(briefing_response)
    @require_auth
    def get(self, user_id):
        try:
            return briefing_service.get_user_briefings(user_id)
        except ValueError as e:
            ns.abort(404, str(e))
        except Exception as e:
            ns.abort(500, str(e))

# Register the namespace
api.add_namespace(ns) 