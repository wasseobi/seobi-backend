from flask_restx import fields

def register_models(ns):
    insight_model = ns.model('InsightSummary', {
        'id': fields.String(description='인사이트 기사 ID'),
        'title': fields.String(description='제목'),
        'created_at': fields.String(description='생성일시(ISO8601)'),
    })

    insight_create = ns.model('InsightCreate', {
        'user_id': fields.String(required=True, description='유저 ID'),
    })

    insight_detail = ns.model('InsightDetail', {
        'id': fields.String(description='인사이트 기사 ID'),
        'title': fields.String(description='제목'),
        'content': fields.Raw(description='본문 및 TTS 스크립트(json)'),
        'created_at': fields.String(description='생성일시(ISO8601)'),
        'keywords': fields.Raw(description='사용된 키워드 리스트'),
        'interest_ids': fields.Raw(description='사용된 interest id 리스트'),
        'type': fields.String(description='생성 유형(chat/report)'),
        'tags': fields.Raw(description='태그'),
        'source': fields.Raw(description='생성 소스'),
    })
    return insight_model, insight_create, insight_detail