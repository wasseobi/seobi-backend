from flask_restx import fields as api_fields

# API documentation models
def register_models(ns):
    """Register all session models with the given namespace"""
    session_model = ns.model('Session', {
        'id': api_fields.String(readonly=True, description='Session UUID'),
        'user_id': api_fields.String(required=True, description='User UUID'),
        'start_at': api_fields.DateTime(readonly=True, description='Session start time'),
        'finish_at': api_fields.DateTime(description='Session finish time', required=False),
        'title': api_fields.String(description='Session title', required=False),
        'description': api_fields.String(description='Session description', required=False)
    })

    session_input = ns.model('SessionInput', {
        'user_id': api_fields.String(required=True, description='User UUID')
    })

    session_update = ns.model('SessionUpdate', {
        'title': api_fields.String(description='Session title'),
        'description': api_fields.String(description='Session description'),
        'finish_at': api_fields.DateTime(description='Session finish time')
    })

    return session_model, session_input, session_update 