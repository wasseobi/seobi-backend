from sqlalchemy_utils import database_exists, create_database, drop_database
from app import db
from sqlalchemy import text

def setup_test_database(app):
    """테스트 데이터베이스 설정을 담당하는 함수"""
    with app.app_context():
        db_uri = app.config['SQLALCHEMY_DATABASE_URI']
        
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