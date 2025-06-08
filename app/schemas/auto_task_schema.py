from flask_restx import fields as api_fields


def register_models(ns):

    auto_task_model = ns.model('AutoTask', {
        'id': api_fields.String(readonly=True, description='AutoTask UUID'),
        'user_id': api_fields.String(required=True, description='User UUID'),
        'title': api_fields.String(required=True, description='업무 제목'),
        'description': api_fields.String(required=False, description='업무 설명 (상세 설명)'),
        'task_list': api_fields.Raw(required=False, description='종속성 업무 목록 (JSON)'),
        'repeat': api_fields.String(required=False, description='반복 조건 (cron 등)'),
        'created_at': api_fields.DateTime(readonly=True, description='생성 시간'),
        'start_at': api_fields.DateTime(required=False, description='시작 시간'),
        'finish_at': api_fields.DateTime(required=False, description='종료 시간'),
        'preferred_at': api_fields.DateTime(required=False, description='선호 실행 시간 (예: 매일 7시)'),
        'active': api_fields.Boolean(required=False, description='활성화/비활성화 상태', default=True),
        'tool': api_fields.String(required=False, description='사용 도구'),
        'linked_service': api_fields.String(required=False, description='연동된 서비스'),
        'current_step': api_fields.String(required=False, description='현재 실행 중인 단계 ID'),
        'status': api_fields.String(required=True, description='업무 상태', 
            enum=['undone', 'doing', 'done', 'failed', 'cancelled']),
        'output': api_fields.Raw(required=False, description='업무 실행 결과 (JSON)'),
        'meta': api_fields.Raw(required=False, description='추가 메타데이터 (JSON)')
    })
    create_auto_task_model = ns.model('AutoTaskCreate', {
        'title': api_fields.String(required=True, description='업무 제목'),
        'description': api_fields.String(required=False, description='업무 설명 (상세 설명)'),
        'task_list': api_fields.Raw(required=False, description='종속성 업무 목록 (JSON)'),
        'repeat': api_fields.String(required=False, description='반복 조건 (cron 등)'),
        'start_at': api_fields.DateTime(required=False, description='시작 시간'),
        'finish_at': api_fields.DateTime(required=False, description='종료 시간'),
        'preferred_at': api_fields.DateTime(required=False, description='선호 실행 시간 (예: 매일 7시)'),
        'active': api_fields.Boolean(required=False, description='활성화/비활성화 상태', default=True),
        'tool': api_fields.String(required=False, description='사용 도구'),
        'linked_service': api_fields.String(required=False, description='연동된 서비스'),
        'status': api_fields.String(required=True, description='업무 상태', 
            enum=['undone', 'doing', 'done', 'failed', 'cancelled'])
    })
    
    return auto_task_model, create_auto_task_model