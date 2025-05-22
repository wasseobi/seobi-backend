# Seobi Backend

Flask 기반의 백엔드 API 서버입니다. PostgreSQL 데이터베이스를 사용하며, SQLAlchemy를 ORM으로 사용합니다.

[![Python](https://img.shields.io/badge/Python-3.12+-blue.svg)](https://www.python.org)
[![Flask](https://img.shields.io/badge/Flask-3.1.1-lightgrey.svg)](https://flask.palletsprojects.com)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-15+-blue.svg)](https://www.postgresql.org)
[![SQLAlchemy](https://img.shields.io/badge/SQLAlchemy-2.0.41-red.svg)](https://www.sqlalchemy.org)
[![uv](https://img.shields.io/badge/uv-latest-orange.svg)](https://github.com/astral-sh/uv)
[![Swagger](https://img.shields.io/badge/Swagger-3.0-green.svg)](https://swagger.io)

## 7. 향후 개발 계획 및 LangGraph 연동

### LangGraph 기반 AI/도구 호출 시스템 개발 로드맵

#### 1) LangGraph 연동 구조 설계 및 기본 구현
- [ ] `app/langgraph/` 디렉터리 내에 builder, tools, workflow, utils 등 모듈 분리
- [ ] ToolNode 및 반복 tool call 구조 구현 (Azure OpenAI 연동 포함)
- [ ] LLM이 문제 해결 시까지 tool call 반복 및 조건부 분기 로직 적용

#### 2) 서비스/라우트 통합 및 엔드포인트 확장
- [ ] 기존 Flask 서비스(`app/services/`)와 LangGraph 연동 서비스(`langgraph_service.py`) 분리 및 통합
- [ ] `/messages` 등 주요 엔드포인트에서 LangGraph 기반 AI/도구 호출 지원

#### 3) 도구 함수 확장 및 관리
- [ ] 실제 서비스에 필요한 도구 함수(예: 예약, TTS, STT, 외부 API 등) 추가 및 관리
- [ ] 도구 등록/관리 인터페이스 및 문서화

#### 4) 상태 관리 및 대화 세션 확장
- [ ] LangGraph 실행 상태, tool call 결과, 대화 이력 등 세션 기반 관리
- [ ] DB 연동 및 세션별 대화 흐름 저장

#### 5) 테스트 및 예외 처리 강화
- [ ] LangGraph 기반 워크플로우 단위/통합 테스트 작성
- [ ] 도구 실패/예외 상황에 대한 graceful fallback 처리

#### 6) 고도화 및 확장
- [ ] LangGraph 기반 멀티툴 조합, 복합 질의 처리, 실시간/비동기 처리 등 고도화
- [ ] LangGraph 기반 워크플로우 시각화 및 관리 도구 개발

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

## 3. 기술 스택

### Backend
- Python 3.12+
- Flask 3.1.1
- SQLAlchemy 2.0.41
- Pydantic (스키마 검증)
- LangGraph, LangChain (AI/LLM 및 도구 호출)
- OpenAI/Azure OpenAI (LLM API 연동)

### Database
- PostgreSQL 15+
- psycopg2-binary
- pgvector (벡터 연산 확장)

### 개발 및 운영 도구
- uv (패키지 매니저)
- Alembic (DB 마이그레이션)
- GitHub Actions (CI/CD)
- Swagger (API 문서화)
- 인증서 기반 SSL (PostgreSQL 접속)

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

