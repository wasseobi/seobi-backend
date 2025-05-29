"""Insight(인사이트) 관련 라우트를 정의하는 모듈입니다."""
from flask import request
from flask_restx import Resource, Namespace
from app.services.insight_article_service import InsightArticleService
from app.schemas.insight_schema import register_models  # insight용 schema 필요
from app.utils.auth_middleware import require_auth
from app import api
import uuid
import logging

# Create namespace
ns = Namespace('insights', description='Insight operations for AI-generated articles')

# Register models for documentation
insight_model, insight_create, insight_detail = register_models(ns)

insight_service = InsightArticleService()

# 디버그용 로거 설정
insight_logger = logging.getLogger("insight_debug")
insight_logger.setLevel(logging.DEBUG)
if not insight_logger.handlers:
    fh = logging.FileHandler("insight_debug.log", encoding="utf-8")
    fh.setLevel(logging.DEBUG)
    formatter = logging.Formatter('%(asctime)s %(levelname)s %(message)s')
    fh.setFormatter(formatter)
    insight_logger.addHandler(fh)

@ns.route('/')
class InsightList(Resource):
    @ns.doc('list_insights', description='List all insights for a user (최신순)')
    @ns.param('user_id', 'User ID for filtering')
    @ns.marshal_list_with(insight_model)
    @require_auth
    def get(self):
        user_id = request.args.get('user_id')
        articles = insight_service.get_user_articles_by_date(user_id)
        return [
            {"id": str(a.id), "title": a.title, "created_at": a.created_at.isoformat()} for a in articles
        ]

@ns.route('/<uuid:article_id>')
@ns.param('article_id', 'The insight article identifier')
@ns.response(404, 'Insight not found')
class InsightDetail(Resource):
    @ns.doc('get_insight', description='Get a single insight article by ID')
    @ns.marshal_with(insight_detail)
    @require_auth
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

@ns.route('/generate')
class InsightGenerate(Resource):
    @ns.doc('generate_insight', description='user_id로 인사이트 그래프를 실행하여 인사이트 결과를 반환합니다.')
    @ns.expect(insight_create)
    @ns.marshal_with(insight_detail, code=201)
    @require_auth
    def post(self):
        user_id = request.json.get('user_id')
        try:
            insight_logger.debug(f"[INSIGHT GENERATE] user_id={user_id}")
            article = insight_service.create_article(user_id, type="report")
            # article이 SQLAlchemy 모델 객체라면 dict로 변환
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
            insight_logger.debug(f"[INSIGHT GENERATE RESULT] {result}")
            return result, 201
        except Exception as e:
            import traceback
            tb = traceback.format_exc()
            insight_logger.error(f"[INSIGHT ERROR] {str(e)}\n{tb}")
            ns.abort(500, f"Insight 생성 중 오류: {str(e)}")

# Register the namespace
api.add_namespace(ns)
