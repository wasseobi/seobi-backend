import os
import sys
import pytest
from app import create_app, db
from tests.db_setup import setup_test_database, teardown_test_database

# Add project root directory to Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

@pytest.fixture(scope='session')
def app():
    """Create and configure a Flask app for testing"""
    app = create_app('testing')
    setup_test_database(app)
    yield app
    teardown_test_database(app)

@pytest.fixture
def client(app):
    """Create a test client for the app"""
    return app.test_client() 