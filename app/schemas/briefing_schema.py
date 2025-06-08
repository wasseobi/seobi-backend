from flask_restx import fields

def register_models(ns):
    """Register all briefing models with the given namespace"""
    briefing_create = ns.model('BriefingCreate', {
        'user_id': fields.String(required=True, description='User UUID', example='a1b2c3d4-5678-4e12-9f34-abcdef123456'),
        'content': fields.String(required=True, description='Briefing content', example='오늘의 브리핑 내용'),
        'script': fields.String(required=False, description='Briefing script', example='브리핑 스크립트')
    })

    briefing_update = ns.model('BriefingUpdate', {
        'content': fields.String(description='Briefing content to update', example='수정된 브리핑 내용'),
        'script': fields.String(description='Briefing script to update', example='수정된 브리핑 스크립트')
    })

    briefing_response = ns.model('BriefingResponse', {
        'id': fields.String(description='Briefing UUID', example='b1c2d3e4-5678-4e12-9f34-abcdef654321'),
        'user_id': fields.String(description='User UUID', example='a1b2c3d4-5678-4e12-9f34-abcdef123456'),
        'content': fields.String(description='Briefing content', example='오늘의 브리핑 내용'),
        'script': fields.String(description='Briefing script', example='브리핑 스크립트'),
        'created_at': fields.String(description='Created at (ISO8601)', example='2024-05-01T12:34:56.789Z')
    })

    return briefing_create, briefing_update, briefing_response 