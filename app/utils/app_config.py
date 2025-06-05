"""Flask 애플리케이션 설정 관련 유틸리티 함수들을 제공합니다."""
from functools import lru_cache

# Global config dictionary to store settings
_config = {
    'DEV_MODE': False,
    'GOOGLE_WEB_CLIENT_ID': None,
    'JWT_SECRET_KEY': None,
    'JWT_ACCESS_TOKEN_EXPIRES': None,
    'AZURE_OPENAI_DEPLOYMENT_NAME': None,
    'AZURE_OPENAI_ENDPOINT': None,
    'AZURE_OPENAI_API_KEY': None,
    'AZURE_OPENAI_API_VERSION': None,
    'AZURE_OPENAI_EMBEDDING_DEPLOYMENT_NAME': None,
    'REDIS_URL': None,
    'REDIS_KEY': None,
    'REDIS_PORT': None
}


def init_config(app):
    """애플리케이션 설정을 초기화합니다."""
    global _config
    _config.update({
        'DEV_MODE': app.config.get('DEV_MODE', False),
        'GOOGLE_WEB_CLIENT_ID': app.config.get('GOOGLE_WEB_CLIENT_ID'),
        'JWT_SECRET_KEY': app.config.get('JWT_SECRET_KEY'),
        'JWT_ACCESS_TOKEN_EXPIRES': app.config.get('JWT_ACCESS_TOKEN_EXPIRES'),
        'AZURE_OPENAI_DEPLOYMENT_NAME': app.config.get('AZURE_OPENAI_DEPLOYMENT_NAME'),
        'AZURE_OPENAI_ENDPOINT': app.config.get('AZURE_OPENAI_ENDPOINT'),
        'AZURE_OPENAI_API_KEY': app.config.get('AZURE_OPENAI_API_KEY'),
        'AZURE_OPENAI_API_VERSION': app.config.get('AZURE_OPENAI_API_VERSION'),
        'AZURE_OPENAI_EMBEDDING_DEPLOYMENT_NAME': app.config.get('AZURE_OPENAI_EMBEDDING_DEPLOYMENT_NAME')
    })


@lru_cache(maxsize=1)
def get_security_config():
    """보안 설정을 반환합니다. 캐싱을 통해 성능을 최적화합니다."""
    return {
        'security': 'Bearer' if not _config['DEV_MODE'] else None,
        'auth_required': not _config['DEV_MODE']
    }


@lru_cache(maxsize=1)
def get_openai_config():
    """OpenAI 관련 설정을 반환합니다."""
    return {
        'deployment_name': _config['AZURE_OPENAI_DEPLOYMENT_NAME'],
        'endpoint': _config['AZURE_OPENAI_ENDPOINT'],
        'api_key': _config['AZURE_OPENAI_API_KEY'],
        'api_version': _config['AZURE_OPENAI_API_VERSION'],
        'embedding_deployment_name': _config['AZURE_OPENAI_EMBEDDING_DEPLOYMENT_NAME']
    }


@lru_cache(maxsize=1)
def get_auth_config():
    """인증 관련 설정을 반환합니다."""
    return {
        'google_web_client_id': _config['GOOGLE_WEB_CLIENT_ID'],
        'jwt_secret_key': _config['JWT_SECRET_KEY'],
        'jwt_access_token_expires': _config['JWT_ACCESS_TOKEN_EXPIRES']
    }


@lru_cache(maxsize=1)
def get_redis_config():
    """Redis 관련 설정을 반환합니다."""
    return {
        'redis_url': _config['REDIS_URL'],
        'redis_key': _config['REDIS_KEY'],
        'redis_port': _config['REDIS_PORT']
    }


def is_dev_mode():
    """개발 모드 여부를 반환합니다."""
    return _config['DEV_MODE']
