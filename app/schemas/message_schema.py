from flask_restx import fields as api_fields

def register_models(ns):
    """Register all message models with the given namespace"""
    message_model = ns.model('Message', {
        'id': api_fields.String(readonly=True, description='Message UUID', example='123e4567-e89b-12d3-a456-426614174000'),
        'session_id': api_fields.String(required=True, description='Session UUID', example='123e4567-e89b-12d3-a456-426614174000'),
        'user_id': api_fields.String(required=True, description='User UUID', example='123e4567-e89b-12d3-a456-426614174000'),
        'content': api_fields.String(required=True, description='Message content', example='안녕하세요, 도움이 필요합니다.'),
        'role': api_fields.String(required=True, description='Message role (user/assistant/system/tool)', example='user', enum=['user', 'assistant', 'system', 'tool']),
        'timestamp': api_fields.DateTime(readonly=True, description='Creation timestamp'),
        'vector': api_fields.List(api_fields.Float, description='Message vector embedding', required=False)
    })

    message_input = ns.model('MessageInput', {
        'session_id': api_fields.String(required=True, description='Session UUID', example='123e4567-e89b-12d3-a456-426614174000'),
        'user_id': api_fields.String(required=True, description='User UUID', example='123e4567-e89b-12d3-a456-426614174000'),
        'content': api_fields.String(required=True, description='Message content', example='파이썬으로 웹 서버를 만드는 방법을 알려주세요.'),
        'role': api_fields.String(required=True, description='Message role', example='user', enum=['user', 'assistant', 'system', 'tool'])
    })

    message_update = ns.model('MessageUpdate', {
        'content': api_fields.String(description='Message content'),
        'role': api_fields.String(description='Message role (user/assistant/system/tool)')
    })

    completion_input = ns.model('CompletionInput', {
        'user_id': api_fields.String(required=True, description='User UUID', example='123e4567-e89b-12d3-a456-426614174000'),
        'content': api_fields.String(required=True, description='Message to send to AI', example='파이썬으로 웹 서버를 만드는 방법을 알려주세요.')
    })

    completion_response = ns.model('CompletionResponse', {
        'user_message': api_fields.Nested(message_model, description='The user message that was sent'),
        'assistant_message': api_fields.Nested(message_model, description='The AI assistant\'s response')
    })

    return message_model, message_input, message_update, completion_input, completion_response 