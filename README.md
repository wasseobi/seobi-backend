# Seobi Backend

Flask 기반의 백엔드 API 서버입니다. PostgreSQL 데이터베이스를 사용하며, SQLAlchemy를 ORM으로 사용합니다.

[![Python](https://img.shields.io/badge/Python-3.12+-blue.svg)](https://www.python.org)
[![Flask](https://img.shields.io/badge/Flask-3.1.1-lightgrey.svg)](https://flask.palletsprojects.com)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-15+-blue.svg)](https://www.postgresql.org)
[![SQLAlchemy](https://img.shields.io/badge/SQLAlchemy-2.0.41-red.svg)](https://www.sqlalchemy.org)
[![uv](https://img.shields.io/badge/uv-latest-orange.svg)](https://github.com/astral-sh/uv)
[![Swagger](https://img.shields.io/badge/Swagger-3.0-green.svg)](https://swagger.io)

## 1. 프로젝트 구조

```
seobi-backend/
│
├── app/
│   ├── __init__.py         # Flask 앱 생성 및 확장자 초기화
│   ├── routes/             # API 엔드포인트 모음
│   │   ├── __init__.py
│   │   ├── user.py         # 사용자 관리 API
│   │   ├── session.py      # 세션 관리 API
│   │   ├── message.py      # 메시지 관리 API
│   │   ├── mcp_server.py   # MCP 서버 관리 API
│   │   └── mcp_server_activation.py # MCP 서버 활성화 관리 API
│   └── models/             # 데이터베이스 모델 정의
│
├── migrations/             # 데이터베이스 마이그레이션
├── main.py                # 애플리케이션 진입점
├── config.py              # 환경 설정
├── requirements.txt       # 프로젝트 의존성
└── pyproject.toml         # 프로젝트 메타데이터
```

## 2. 주요 기능

- 사용자 관리 (User CRUD)
- 세션 관리 (Session CRUD)
- 메시지 관리 (Message CRUD)
- MCP 서버 관리 (MCPServer CRUD)
- MCP 서버 활성화 관리 (ActiveMCPServer CRUD)

## 3. 기술 스택

### Backend
- ![Python](https://img.shields.io/badge/Python-3.12+-blue.svg) - 프로그래밍 언어
- ![Flask](https://img.shields.io/badge/Flask-3.1.1-lightgrey.svg) - 웹 프레임워크
- ![SQLAlchemy](https://img.shields.io/badge/SQLAlchemy-2.0.41-red.svg) - ORM

### Database
- ![PostgreSQL](https://img.shields.io/badge/PostgreSQL-15+-blue.svg) - 관계형 데이터베이스
- ![psycopg2](https://img.shields.io/badge/psycopg2--binary-2.9.10-blue.svg) - PostgreSQL 어댑터
- ![pgvector](https://img.shields.io/badge/pgvector-0.4.1-blue.svg) - 벡터 연산 확장

### Development Tools
- ![uv](https://img.shields.io/badge/uv-latest-orange.svg) - 패키지 매니저
- ![GitHub Actions](https://img.shields.io/badge/GitHub_Actions-2088FF.svg?logo=github-actions&logoColor=white) - CI/CD
- ![Alembic](https://img.shields.io/badge/Alembic-1.15.2-blue.svg) - 데이터베이스 마이그레이션 도구


## 4. 시작하기

### 환경 설정

1. Python 3.12 설치
2. uv 설치
   ```bash
   pip install uv
   ```
3. 환경 변수 설정
   - `.env` 파일을 root directory에 생성 및 설정(설정값은 팀원에게 확인)
   - `.certificate.pem` 파일을 root directory에 저장(파일 요청은 팀원에게 문의)

### 가상환경 활성화

```bash
# 가상환경 생성
uv venv

# 가상환경 활성화
source .venv/bin/activate
```

### 의존성 설치

```bash
uv sync
```

### 데이터베이스 마이그레이션

```bash
flask db upgrade
```

### 서버 실행

```bash
python main.py
```

## 5. API 엔드포인트

각 기능별로 다음과 같은 엔드포인트가 구현되어 있습니다:

- `/users`: 사용자 관리
- `/sessions`: 세션 관리
- `/messages`: 메시지 관리
- `/mcp_servers`: MCP 서버 관리
- `/mcp_server_activations`: MCP 서버 활성화 관리

### API 문서화 (Swagger UI)

API 문서는 Swagger UI를 통해 제공됩니다:

- URL: `http://localhost:5000/docs`
- 기능:
  - 모든 API 엔드포인트 목록 및 상세 설명
  - 요청/응답 모델 스키마
  - API 테스트 인터페이스
  - 인증이 필요한 엔드포인트의 경우 인증 토큰 입력 가능

API 문서는 Flask-RESTX를 사용하여 자동으로 생성되며, 각 엔드포인트의 코드에 포함된 데코레이터와 docstring을 기반으로 문서가 생성됩니다.

## 6. 개발 가이드

### 코드 스타일

- Python 코드는 PEP 8 스타일 가이드를 따릅니다.
- 모든 새로운 기능은 테스트 코드를 포함해야 합니다.

### 브랜치 전략

- `main`: 프로덕션 브랜치
- `develop`: 개발 브랜치
- `feature/*`: 새로운 기능 개발
- `hotfix/*`: 긴급 버그 수정
