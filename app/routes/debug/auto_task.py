from flask_restx import Namespace, Resource
from app.services.auto_task_sevice import AutoTaskService
from app.schemas.auto_task_schema import register_models
from app.utils.auth_middleware import require_auth
from app import api

ns = Namespace('autotask', description='자동 업무 API')

auto_task_model, create_auto_task_model = register_models(ns)
auto_task_service = AutoTaskService()

@ns.route('/')
class AutoTaskList(Resource):
    @ns.doc('list_auto_task')
    @ns.marshal_list_with(auto_task_model)
    @require_auth
    def get(self):
        return auto_task_service.get_all_auto_tasks()
    
    @ns.doc('create_auto_task')
    @ns.expect(create_auto_task_model)
    @ns.marshal_with(auto_task_model)
    @require_auth
    def post(self):
        try:
            data = api.payload
            user_id = data.get('user_id')
            if not user_id:
                ns.abort(400, 'user_id is required')
            # user_id는 별도 파라미터로, 나머지는 dict로 전달
            data = {k: v for k, v in data.items() if k != 'user_id'}
            return auto_task_service.create(user_id, data)
        except ValueError as e:
            ns.abort(400, str(e))

@ns.route('/<uuid:auto_task_id>')
@ns.param('auto_task_id', 'The auto_task identifier')
@ns.response(404, 'AutoTask not found')
class AutoTaskResource(Resource):
    @ns.doc('get_auto_task')
    @ns.marshal_with(auto_task_model)
    @require_auth
    def get(self, auto_task_id):
        try:
            return auto_task_service.get_auto_task_by_id(auto_task_id)
        except ValueError as e:
            ns.abort(404, str(e))

    @ns.doc('update_auto_task')
    @ns.expect(create_auto_task_model)
    @ns.marshal_with(auto_task_model)
    @require_auth
    def put(self, auto_task_id):
        try:
            data = api.payload
            return auto_task_service.update(auto_task_id, **data)
        except ValueError as e:
            ns.abort(404, str(e))

    @ns.doc('delete_auto_task')
    @require_auth
    def delete(self, auto_task_id):
        try:
            result = auto_task_service.delete(auto_task_id)
            return {'result': result}
        except ValueError as e:
            ns.abort(404, str(e))

@ns.route('/user/<uuid:user_id>')
@ns.param('user_id', 'The user identifier')
class UserAutoTask(Resource):
    @ns.doc('get_user_auto_task')
    @ns.marshal_list_with(auto_task_model)
    def get(self, user_id):
        try:
            return auto_task_service.get_user_auto_tasks(user_id)
        except ValueError as e:
            ns.abort(404, str(e))

    @ns.doc('create_auto_task')
    @ns.expect(create_auto_task_model)
    @ns.marshal_with(auto_task_model)
    @require_auth
    def post(self, user_id):
        try:
            data = api.payload
            return auto_task_service.create(user_id, data)
        except ValueError as e:
            ns.abort(400, str(e))
