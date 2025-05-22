import os
from urllib.parse import quote_plus

class Config:
    # Development mode configuration
    DEV_MODE = os.getenv("DEV_MODE", "True").lower() == "true"

    # Database configuration
    DB_USER = os.getenv("PGUSER")
    DB_PASS = quote_plus(os.getenv("PGPASSWORD"))
    DB_HOST = os.getenv("PGHOST")
    DB_PORT = os.getenv("PGPORT")
    DB_NAME = os.getenv("PGDATABASE")
    SSL_CERT = os.getenv("PGSSLROOTCERT")
    SQLALCHEMY_DATABASE_URI = (
        f"postgresql+psycopg2://{DB_USER}:{DB_PASS}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
        f"?sslmode=require&sslrootcert={SSL_CERT}"
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # Azure OpenAI Configuration
    AZURE_OPENAI_API_KEY = os.getenv("AZURE_OPENAI_API_KEY")
    AZURE_OPENAI_API_VERSION = os.getenv("AZURE_OPENAI_API_VERSION")
    AZURE_OPENAI_ENDPOINT = os.getenv("AZURE_OPENAI_ENDPOINT")
    AZURE_OPENAI_DEPLOYMENT_NAME = os.getenv("AZURE_OPENAI_DEPLOYMENT_NAME")
    AZURE_OPENAI_EMBEDDING_DEPLOYMENT_NAME = os.getenv("AZURE_OPENAI_EMBEDDING_DEPLOYMENT_NAME")
    
    # Google Search API Configuration
    GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
    GOOGLE_CSE_ID = os.getenv("GOOGLE_CSE_ID")

    # JWT Configuration
    JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY", "dev_jwt_secret_key")
    SECRET_KEY = os.getenv("SECRET_KEY", "dev_flask_secret_key")
    JWT_ACCESS_TOKEN_EXPIRES = int(os.getenv("JWT_ACCESS_TOKEN_EXPIRES"))
    
class TestConfig(Config):
    """Test configuration."""
    TESTING = True
    DB_NAME = "seobi_test"
    SQLALCHEMY_DATABASE_URI = (
        f"postgresql+psycopg2://{Config.DB_USER}:{Config.DB_PASS}@{Config.DB_HOST}:{Config.DB_PORT}/{DB_NAME}"
        f"?sslmode=require&sslrootcert={Config.SSL_CERT}"
    )
    