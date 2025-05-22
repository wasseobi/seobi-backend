from flask_restx import fields

def register_models(ns):
    """Register all user models with the given namespace"""
    user_create = ns.model('UserCreate', {
        'username': fields.String(required=True, description='Username', example='testuser'),
        'email': fields.String(required=True, description='Email address', example='test@example.com')
    })

    user_update = ns.model('UserUpdate', {
        'username': fields.String(description='Username to update', example='updated_username'),
        'email': fields.String(description='Email address to update', example='updated@example.com')
    })

    user_response = ns.model('UserResponse', {
        'id': fields.String(description='User UUID', example='a1b2c3d4-5678-4e12-9f34-abcdef123456'),
        'username': fields.String(required=True, description='Username', example='testuser'),
        'email': fields.String(required=True, description='Email address', example='test@example.com')
    })

    return user_create, user_update, user_response