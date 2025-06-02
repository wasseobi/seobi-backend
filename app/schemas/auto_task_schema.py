from flask_restx import fields as api_fields


def register_models(ns):

    auto_task_model = ns.model('AutoTask', {
        'id': api_fields.String(readonly=True, description='AutoTask UUID'),
        'user_id': api_fields.String(required=True, description='User UUID'),
        'title': api_fields.String(required=True, description='AutoTask title'),
        'repeat': api_fields.String(required=False, description='AutoTask repeat'),
        'created_at': api_fields.DateTime(readonly=True, description='AutoTask created time'),
        'start_at': api_fields.DateTime(required=False, description='AutoTask start time'),
        'finish_at': api_fields.DateTime(required=False, description='AutoTask finish time'),
        'tool': api_fields.String(required=True, description='AutoTask tool'),
        'status': api_fields.String(required=True, description='AutoTask ststus(undone/done)', enum=['undone', 'done']),
        'linked_service': api_fields.String(required=False, description='AutoTask linked_service')
    })
    create_auto_task_model = ns.model('AutoTaskCreate', {
        'title': api_fields.String(required=True, description='AutoTask title'),
        'repeat': api_fields.String(required=False, description='AutoTask repeat'),
        'start_at': api_fields.DateTime(required=False, description='AutoTask start time'),
        'finish_at': api_fields.DateTime(required=False, description='AutoTask finish time'),
        'tool': api_fields.String(required=True, description='AutoTask tool'),
        'status': api_fields.String(required=True, description='AutoTask status(undone/done)', enum=['undone', 'done']),
        'linked_service': api_fields.String(required=False, description='AutoTask linked_service')
    })
    
    return auto_task_model, create_auto_task_model