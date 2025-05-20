import os
from urllib.parse import quote_plus

class Config:
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