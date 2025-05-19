from flask import Flask
from flask_migrate import Migrate
from dotenv import load_dotenv
from urllib.parse import quote_plus
import os

# .env 파일 로드
load_dotenv()

from models import db

app = Flask(__name__)

DB_USER = os.getenv("PGUSER")
DB_PASS = quote_plus(os.getenv("PGPASSWORD"))
DB_HOST = os.getenv("PGHOST")
DB_PORT = os.getenv("PGPORT")
DB_NAME = os.getenv("PGDATABASE")
SSL_CERT = os.getenv("PGSSLROOTCERT")

# PostgreSQL 데이터베이스 설정
SQLALCHEMY_DATABASE_URI = (
    f"postgresql+psycopg2://{DB_USER}:{DB_PASS}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
    f"?sslmode=require&sslrootcert={SSL_CERT}"
)
app.config["SQLALCHEMY_DATABASE_URI"] = SQLALCHEMY_DATABASE_URI
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db.init_app(app)
migrate = Migrate(app, db)

# Flask 실행
if __name__ == '__main__':
    app.run(debug=True)