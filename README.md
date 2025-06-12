# Seobi Backend

Flask 기반의 백엔드 API 서버입니다. PostgreSQL 데이터베이스를 사용하며, SQLAlchemy를 ORM으로 사용합니다.

## 7. 향후 개발 계획 및 LangGraph 연동

### LangGraph 기반 AI/도구 호출 시스템 개발 로드맵


---

이후 LangGraph 관련 코드는 `app/langgraph/` 폴더에 집중 관리하며, 기존 서비스와의 통합 및 확장성을 고려해 개발을 진행할 예정입니다.

## 1. 프로젝트 구조

```
seobi-backend/
│
├── app/
│   ├── __init__.py
│   ├── dao/                  # 데이터 접근 객체(DAO) 모음
│   │   ├── base.py
│   │   └── user_dao.py
│   ├── langgraph/            # LangGraph 연동 및 도구 관련 코드
│   ├── models/               # 데이터베이스 모델 정의
│   │   ├── __init__.py
│   │   ├── db.py
│   │   ├── mcp_server.py
│   │   ├── mcp_server_activation.py
│   │   ├── message.py
│   │   ├── session.py
│   │   └── user.py
│   ├── routes/               # API 엔드포인트
│   │   ├── __init__.py
│   │   ├── mcp_server.py
│   │   ├── mcp_server_activation.py
│   │   ├── message.py
│   │   ├── session.py
│   │   └── user.py
│   ├── schemas/              # Pydantic 등 스키마 정의
│   │   └── user_schema.py
│   ├── services/             # 비즈니스 로직
│   │   └── user_service.py
│   └── utils/                # 유틸리티 함수 및 외부 연동
│       └── openai_client.py
│
├── certs/                    # 인증서 등 보안 관련 파일
│   └── certificate.pem
├── migrations/               # Alembic 마이그레이션
│   ├── alembic.ini
│   ├── env.py
│   ├── README
│   ├── script.py.mako
│   └── versions/
├── config.py                 # 환경 설정
├── main.py                   # 애플리케이션 진입점
├── requirements.txt          # 의존성 목록
├── pyproject.toml            # 프로젝트 메타데이터
└── uv.lock                   # uv 패키지 매니저 lock 파일
```

## 2. 주요 기능

- 사용자 관리 (User CRUD)
- 세션 관리 (Session CRUD)
- 메시지 관리 (Message CRUD)
- MCP 서버 관리 (MCPServer CRUD)
- MCP 서버 활성화 관리 (ActiveMCPServer CRUD)
- 일정 관리 (Schedule CRUD)
- 리포트 관리 (Report CRUD)
- 인사이트 아티클 관리 (InsightArticle CRUD)

## 3. 기술 스택

### Backend

![Microsoft Azure](https://img.shields.io/badge/azure-%230072C6.svg?style=for-the-badge&logo=msazure&logoColor=white)
![Python](https://img.shields.io/badge/python-3670A0?style=for-the-badge&logo=python&logoColor=ffdd54)
![Flask](https://img.shields.io/badge/flask-%23000.svg?style=for-the-badge&logo=flask&logoColor=white)
![SQLAlchemy](https://img.shields.io/badge/SQLAlchemy-D71F00.svg?style=for-the-badge&logo=SQLAlchemy&logoColor=white)
![Pydantic](https://img.shields.io/badge/Pydantic-E92063.svg?style=for-the-badge&logo=Pydantic&logoColor=white)
![LangGraph](https://img.shields.io/badge/LangGraph-1C3C3C.svg?style=for-the-badge&logo=LangGraph&logoColor=white)
![LangChain](https://img.shields.io/badge/LangChain-1C3C3C.svg?style=for-the-badge&logo=LangChain&logoColor=white)
![OpenAI](https://img.shields.io/badge/OpenAI-412991.svg?style=for-the-badge&logo=OpenAI&logoColor=white)

### Dev & Ops

![UV](https://img.shields.io/badge/uv-DE5FE9.svg?style=for-the-badge&logo=uv&logoColor=white)
![Github-Actions](https://img.shields.io/badge/GitHub%20Actions-2088FF.svg?style=for-the-badge&logo=GitHub-Actions&logoColor=white)
![Swagger](https://img.shields.io/badge/Swagger-85EA2D.svg?style=for-the-badge&logo=Swagger&logoColor=black)
![OpenSSL](https://img.shields.io/badge/OpenSSL-721412.svg?style=for-the-badge&logo=OpenSSL&logoColor=white)
![Postgresql](https://img.shields.io/badge/PostgreSQL-4169E1.svg?style=for-the-badge&logo=PostgreSQL&logoColor=white)

### Database

![Postgres](https://img.shields.io/badge/postgres-%23316192.svg?style=for-the-badge&logo=postgresql&logoColor=white)

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
flask db history
flask db migrate -m "적고 싶은 메세지(수정관련 내용)" 
flask db upgrade
```

#### 새 DB로의 마이그레이션 시,
- flask db history를 통해 지금 마이그레이션 파일이 존재하는지 확인.
- 이후, config의 DB_HOST = os.getenv("PGHOST") 제대로 된 값으로 변경된 것이 맞는지 확인까지 마친 뒤 마이그레이션 부탁드립니다.


### 서버 실행

```bash
python main.py
```

### 패키지 관리

- 개발하면서 추가된 패키지가 있다면 아래 명령어로 패키지 정리 진행 필수

```bash
uv export -o requirements.txt
```

### flask 개발 모드 관련

`DEV_MODE=True`
개발모드 시, JWT 토큰 필요 없음. 배포 시, False로 수정하여 JWT 토큰 검증 이후에 백엔드 API 호출 가능합니다.

## 5. API 엔드포인트

각 기능별로 다음과 같은 엔드포인트가 구현되어 있습니다:

- `/users`: 사용자 관리
- `/sessions`: 세션 관리
- `/messages`: 메시지 관리
- `/mcp_servers`: MCP 서버 관리
- `/mcp_server_activations`: MCP 서버 활성화 관리
- `/schedule`: 일정 관리
- `/report`: 리포트 관리
- `/insight_article`: 인사이트 아티클 관리

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
