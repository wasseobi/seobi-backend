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

@pytest.mark.run(order=1)  # DB 설정(1) -> 모델(2) -> DAO(3) -> Service(4) -> Route(5) -> DB 정리(6)
def test_database_permissions(app):
    """테스트 데이터베이스 사용자 권한 설정 테스트"""
    with app.app_context():
        # 현재 사용자의 권한 확인
        db_user = app.config['DB_USER']
        db_name = app.config['DB_NAME']
        
        # 사용자가 데이터베이스에 접근 권한이 있는지 확인
        result = db.session.execute(text("""
            SELECT has_database_privilege(:user, :db, 'CONNECT')
        """), {'user': db_user, 'db': db_name}).scalar()
        assert result is True, f"User {db_user} does not have CONNECT privilege on {db_name}"
        
        # 사용자가 테이블에 대한 권한이 있는지 확인
        for table in ['user', 'session', 'message', 'mcp_server', 'mcp_server_activation']:
            # SELECT 권한 확인
            result = db.session.execute(text("""
                SELECT has_table_privilege(:user, :table, 'SELECT')
            """), {'user': db_user, 'table': table}).scalar()
            assert result is True, f"User {db_user} does not have SELECT privilege on {table}"
            
            # INSERT 권한 확인
            result = db.session.execute(text("""
                SELECT has_table_privilege(:user, :table, 'INSERT')
            """), {'user': db_user, 'table': table}).scalar()
            assert result is True, f"User {db_user} does not have INSERT privilege on {table}"
            
            # UPDATE 권한 확인
            result = db.session.execute(text("""
                SELECT has_table_privilege(:user, :table, 'UPDATE')
            """), {'user': db_user, 'table': table}).scalar()
            assert result is True, f"User {db_user} does not have UPDATE privilege on {table}"
            
            # DELETE 권한 확인
            result = db.session.execute(text("""
                SELECT has_table_privilege(:user, :table, 'DELETE')
            """), {'user': db_user, 'table': table}).scalar()
            assert result is True, f"User {db_user} does not have DELETE privilege on {table}" 