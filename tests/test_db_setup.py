import pytest
from app import db
from sqlalchemy import text, inspect

@pytest.mark.run(order=1)  # DB 설정(1) -> 모델(2) -> DAO(3) -> Service(4) -> Route(5) -> DB 정리(6)
def test_database_creation(app):
    """테스트 데이터베이스와 테이블 생성 테스트"""
    with app.app_context():
        # 데이터베이스 연결 테스트
        result = db.session.execute(text('SELECT 1')).scalar()
        assert result == 1
        
        # 모든 테이블이 생성되었는지 확인
        inspector = inspect(db.engine)
        tables = inspector.get_table_names()
        expected_tables = ['user', 'session', 'message', 'mcp_server', 'mcp_server_activation']
        assert all(table in tables for table in expected_tables)
        
        # pgvector 확장이 설치되었는지 확인
        result = db.session.execute(text("SELECT 1 FROM pg_extension WHERE extname = 'vector'")).scalar()
        assert result == 1 