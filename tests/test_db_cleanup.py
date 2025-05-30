import pytest
from app import create_app
from sqlalchemy_utils import drop_database, database_exists

@pytest.mark.run(order=6)  # DB 설정(1) -> 모델(2) -> DAO(3) -> Service(4) -> Route(5) -> DB 정리(6)
def test_database_cleanup():
    """Test if the test database can be dropped successfully after all tests"""
    # Create app without database initialization
    app = create_app('testing')
    
    # Get database URI
    db_uri = app.config['SQLALCHEMY_DATABASE_URI']
    
    # Drop the entire database
    if database_exists(db_uri):
        drop_database(db_uri)
    
    # Verify that database is dropped
    assert not database_exists(db_uri), "Database should be dropped but still exists" 