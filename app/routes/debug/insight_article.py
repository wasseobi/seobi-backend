from flask_restx import Namespace, Resource, fields
from app.services.insight_article_service import InsightArticleService
from app.utils.auth_middleware import require_auth

ns = Namespace('insight_article', description='인사이트 아티클 API')

insight_article_model = ns.model('InsightArticle', {
    'id': fields.String,
    'user_id': fields.String,
    'title': fields.String,
    'content': fields.String,
    'tags': fields.List(fields.String),
    'source': fields.String,
})

create_insight_article_model = ns.model('InsightArticleCreate', {
    'user_id': fields.String(required=True),
    'title': fields.String(required=True),
    'content': fields.String(required=True),
    'tags': fields.List(fields.String),
    'source': fields.String(required=True),
})

service = InsightArticleService()

@ns.route('/<uuid:user_id>')
class ArticleList(Resource):
    @ns.marshal_list_with(insight_article_model)
    @require_auth
    def get(self, user_id):
        """특정 사용자의 모든 인사이트 아티클 조회"""
        return service.get_user_articles(user_id)

    @ns.expect(create_insight_article_model)
    @ns.marshal_with(insight_article_model)
    @require_auth
    def post(self, user_id):
        """새 인사이트 아티클 생성"""
        from flask import request
        data = request.json
        data['user_id'] = str(user_id)
        data.pop('id', None)
        return service.create_article(data), 201

@ns.route('/detail/<uuid:article_id>')
class ArticleDetail(Resource):
    @ns.marshal_with(insight_article_model)
    @require_auth
    @ns.response(404, '아티클이 존재하지 않음')
    def get(self, article_id):
        """아티클 상세 조회"""
        article = service.get_article(article_id)
        if not article:
            ns.abort(404, "해당 아티클이 존재하지 않습니다.")
        return article

    @require_auth
    def delete(self, article_id):
        """아티클 삭제"""
        result = service.delete_article(article_id)
        if result:
            return {'result': 'deleted'}
        return {'error': 'not found'}, 404
