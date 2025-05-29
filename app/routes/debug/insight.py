from flask import request, jsonify
from flask_restx import Namespace, Resource, fields
from app.services.insight_article_service import InsightArticleService

ns = Namespace('insight', description='인사이트 생성 및 조회 API')
insight_service = InsightArticleService()

insight_summary = ns.model('InsightSummary', {
    'id': fields.String(description='인사이트 기사 ID'),
    'title': fields.String(description='제목'),
    'created_at': fields.String(description='생성일시(ISO8601)'),
})

insight_detail = ns.model('InsightDetail', {
    'id': fields.String(description='인사이트 기사 ID'),
    'title': fields.String(description='제목'),
    'content': fields.String(description='본문'),
    'created_at': fields.String(description='생성일시(ISO8601)'),
    'keywords': fields.Raw(description='사용된 키워드 리스트'),
    'interest_ids': fields.Raw(description='사용된 interest id 리스트'),
    'type': fields.String(description='생성 유형(chat/report)'),
    'tags': fields.Raw(description='태그'),
    'source': fields.String(description='생성 소스'),
})


@ns.route('/generate')
class InsightGenerate(Resource):
    """user_id로 인사이트 그래프를 실행하여 인사이트 결과를 반환합니다."""
    @ns.doc(description="user_id를 받아 LangGraph 인사이트 그래프를 실행하고 결과를 반환합니다.")
    @ns.expect(ns.model('GenerateRequest', {'user_id': fields.String(required=True)}), validate=True)
    def post(self):
        user_id = request.json.get('user_id')
        article = insight_service.create_article(user_id, type="chat")
        result = {
            "id": str(article.id),
            "title": article.title,
            "content": article.content,
            "tags": article.tags,
            "source": article.source,
            "type": article.type,
            "created_at": article.created_at.isoformat() if article.created_at else None,
            "keywords": article.keywords,
            "interest_ids": article.interest_ids
        }
        return result, 201


@ns.route('/list')
class InsightList(Resource):
    """user_id로 인사이트 기사 목록을 최신순으로 조회합니다."""
    @ns.doc(description="user_id로 인사이트 기사 목록을 최신순으로 반환합니다.")
    @ns.marshal_list_with(insight_summary)
    def get(self):
        user_id = request.args.get('user_id')
        articles = insight_service.get_user_articles_by_date(user_id)
        return [
            {"id": str(a.id), "title": a.title, "created_at": a.created_at.isoformat()} for a in articles
        ]


@ns.route('/<uuid:article_id>')
@ns.param('article_id', '인사이트 기사 ID')
class InsightDetail(Resource):
    """인사이트 기사 단건 상세 조회"""
    @ns.doc(description="article_id로 인사이트 기사 상세 정보를 반환합니다.")
    @ns.marshal_with(insight_detail)
    def get(self, article_id):
        article = insight_service.get_article(article_id)
        if not article:
            ns.abort(404, 'Not found')
        return {
            "id": str(article.id),
            "title": article.title,
            "content": article.content,
            "created_at": article.created_at.isoformat(),
            "keywords": article.keywords,
            "interest_ids": article.interest_ids,
            "type": article.type,
            "tags": article.tags,
            "source": article.source
        }
