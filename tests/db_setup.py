from sqlalchemy_utils import database_exists, create_database, drop_database
from app import db
from sqlalchemy import text
import re
from urllib.parse import urlparse

# 테스트 데이터베이스 이름 고정
TEST_DB_NAME = 'seobi_test'

def validate_test_database_uri(db_uri: str) -> None:
    """테스트 데이터베이스 URI가 안전한지 검증하는 함수"""
    parsed = urlparse(db_uri)
    db_name = parsed.path.lstrip('/')

    # 테스트 DB 이름 검증
    if db_name != TEST_DB_NAME:
        raise ValueError(
            f"Attempting to use non-test database: {db_name}. "
            f"Test database name must be '{TEST_DB_NAME}'"
        )

def setup_test_database(app):
    """테스트 데이터베이스 설정을 담당하는 함수"""
    with app.app_context():
        db_uri = app.config['SQLALCHEMY_DATABASE_URI']
        
        # 테스트 데이터베이스 이름 검증
        validate_test_database_uri(db_uri)
        
        if not database_exists(db_uri):
            create_database(db_uri)
        
        # pgvector 확장 설치
        engine = db.engine
        with engine.connect() as conn:
            conn.execute(text('CREATE EXTENSION IF NOT EXISTS vector;'))
            conn.commit()
        
        # 모든 모델의 테이블을 생성
        db.create_all()
        
        return db_uri

def teardown_test_database(app):
    """테스트 데이터베이스 정리를 담당하는 함수"""
    with app.app_context():
        db_uri = app.config['SQLALCHEMY_DATABASE_URI']
        
        # 테스트 데이터베이스 이름 검증
        validate_test_database_uri(db_uri)
        
        # 모든 연결을 정리
        db.session.remove()
        db.engine.dispose()  # 기존 연결 강제 종료
        
        try:
            # 데이터베이스 삭제 시도
            if database_exists(db_uri):
                drop_database(db_uri)
        except Exception as e:
            print(f"Warning: Error during database cleanup: {e}")
            # 에러가 발생해도 계속 진행
            pass