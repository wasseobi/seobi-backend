from flask_restx import fields as api_fields


def register_models(ns):

    background_model = ns.model('Background', {
        'user_id': api_fields.String(description='유저 UUID', example='123e4567-e89b-12d3-a456-426614174000', required=False),
        'task': api_fields.Raw(description='TaskRuntime 정보 (JSON)', required=False),
        'last_completed_title': api_fields.String(description='마지막 완료 Task 제목', required=False),
        'error': api_fields.String(description='에러 메시지', required=False),
        'finished': api_fields.Boolean(description='백그라운드 실행 완료 여부', required=False),
        'step': api_fields.Raw(description='현재 PlanStep 정보 (JSON)', required=False)
    })
    return background_model