"""Insight(인사이트) 관련 라우트를 정의하는 모듈입니다."""
from flask import request
from flask_restx import Resource, Namespace, fields
from app.services.insight_article_service import InsightArticleService
from app.utils.auth_middleware import require_auth
from app.utils.app_config import is_dev_mode
from app import api
import uuid
import logging

# 로거 설정
log = logging.getLogger("insight")

# Create namespace with detailed description
ns = Namespace(
    'insights', 
    description='AI가 생성한 인사이트 아티클 관련 작업'
)

# Define models for documentation
insight_model = ns.model('InsightArticle', {
    'id': fields.String(description='인사이트 아티클 UUID',
                       example='123e4567-e89b-12d3-a456-426614174000'),
    'title': fields.String(description='아티클 제목',
                          example='최근 관심사 분석 리포트'),
    'created_at': fields.DateTime(description='생성 시간',
                                example='2025-05-23T09:13:11.475Z')
})

insight_detail = ns.model('InsightArticleDetail', {
    'id': fields.String(description='인사이트 아티클 UUID'),
    'title': fields.String(description='아티클 제목'),
    'content': fields.String(description='아티클 내용'),
    'tags': fields.List(fields.String, description='태그 목록'),
    'source': fields.String(description='데이터 소스'),
    'type': fields.String(description='아티클 타입'),
    'created_at': fields.DateTime(description='생성 시간'),
    'keywords': fields.List(fields.String, description='키워드 목록'),
    'interest_ids': fields.List(fields.String, description='관련 관심사 ID 목록')
})

# Initialize service
insight_service = InsightArticleService()


@ns.route('/<uuid:user_id>')
class UserInsights(Resource):
    @ns.doc('사용자의 인사이트 목록',
            description='특정 사용자의 모든 인사이트 아티클 목록을 가져옵니다.',
            security='Bearer' if not is_dev_mode() else None,
            params={
                'Authorization': {
                    'description': 'Bearer <jwt>',
                    'in': 'header',
                    'required': not is_dev_mode()
                }
            })
    @ns.response(200, '인사이트 목록 조회 성공', [insight_model])
    @ns.response(400, '잘못된 요청')
    @ns.response(401, '인증 실패')
    @ns.marshal_list_with(insight_model)
    @require_auth
    def get(self, user_id):
        """특정 사용자의 모든 인사이트 아티클 목록을 가져옵니다."""
        try:
            articles = insight_service.get_user_articles_by_date(user_id)
            return [
                {
                    "id": str(a.id),
                    "title": a.title,
                    "created_at": a.created_at.isoformat()
                } for a in articles
            ]
        except Exception as e:
            log.error(f"Failed to get user insights: {str(e)}")
            ns.abort(400, f"인사이트 목록 조회 실패: {str(e)}")

    @ns.doc('인사이트 생성',
            description='사용자의 데이터를 기반으로 새로운 인사이트 아티클을 생성합니다.',
            security='Bearer' if not is_dev_mode() else None,
            params={
                'Authorization': {
                    'description': 'Bearer <jwt>',
                    'in': 'header',
                    'required': not is_dev_mode()
                }
            })
    @ns.response(201, '인사이트 생성 성공', insight_detail)
    @ns.response(400, '잘못된 요청')
    @ns.response(401, '인증 실패')
    @ns.response(500, '인사이트 생성 중 오류 발생')
    @ns.marshal_with(insight_detail)
    @require_auth
    def post(self, user_id):
        """사용자의 데이터를 기반으로 새로운 인사이트 아티클을 생성합니다."""
        try:
            article = insight_service.create_article(user_id, type="report")
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
        except Exception as e:
            log.error(f"Failed to create insight: {str(e)}")
            ns.abort(500, f"인사이트 생성 중 오류가 발생했습니다: {str(e)}")

@ns.route('/list/<uuid:article_id>')
class InsightArticleDetail(Resource):
    @ns.doc('인사이트 아티클 상세 조회',
            description='특정 인사이트 아티클의 상세 내용을 가져옵니다.',
            security='Bearer' if not is_dev_mode() else None,
            params={
                'Authorization': {
                    'description': 'Bearer <jwt>',
                    'in': 'header',
                    'required': not is_dev_mode()
                }
            })
    @ns.response(200, '아티클 조회 성공', insight_detail)
    @ns.response(400, '잘못된 요청')
    @ns.response(401, '인증 실패')
    @ns.response(404, '아티클을 찾을 수 없음')
    @ns.marshal_with(insight_detail)
    @require_auth
    def get(self, article_id):
        """특정 인사이트 아티클의 상세 내용을 가져옵니다."""
        try:
            article = insight_service.get_article(article_id)
            if not article:
                ns.abort(404, "해당 아티클을 찾을 수 없습니다.")
            
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
            return result
            
        except Exception as e:
            log.error(f"Failed to get article detail: {str(e)}")
            ns.abort(400, f"아티클 조회 실패: {str(e)}")


# Register the namespace
api.add_namespace(ns)