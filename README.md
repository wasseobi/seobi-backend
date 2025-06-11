# Seobi Backend

Flask 기반의 백엔드 API 서버입니다. PostgreSQL 데이터베이스를 사용하며, SQLAlchemy를 ORM으로 사용합니다. LangGraph를 활용한 AI 에이전트 시스템과 다양한 도구 연동을 지원합니다.

## 7. 향후 개발 계획 및 LangGraph 연동

### LangGraph 기반 AI/도구 호출 시스템 개발 로드맵

#### 1) LangGraph 연동 구조 설계 및 기본 구현 ✅

- [x] `app/langgraph/` 디렉터리 내에 builder, tools, workflow, utils 등 모듈 분리
- [x] ToolNode 및 반복 tool call 구조 구현 (Azure OpenAI 연동 포함)
- [x] LLM이 문제 해결 시까지 tool call 반복 및 조건부 분기 로직 적용

#### 2) 서비스/라우트 통합 및 엔드포인트 확장 ✅

- [x] 기존 Flask 서비스(`app/services/`)와 LangGraph 연동 서비스(`langgraph_service.py`) 분리 및 통합
- [x] `/messages` 등 주요 엔드포인트에서 LangGraph 기반 AI/도구 호출 지원

#### 3) 도구 함수 확장 및 관리 🔄

- [x] 기본 도구 함수 구현 (검색, 일정, 날씨, 메모리)
- [x] 실제 서비스에 필요한 추가 도구 함수 구현
- [x] 도구 등록/관리 인터페이스 및 문서화

#### 4) 상태 관리 및 대화 세션 확장 ✅

- [x] LangGraph 실행 상태, tool call 결과, 대화 이력 등 세션 기반 관리
- [x] DB 연동 및 세션별 대화 흐름 저장

#### 5) 테스트 및 예외 처리 강화 🔄

- [x] LangGraph 기반 워크플로우 단위/통합 테스트 작성
- [x] 도구 실패/예외 상황에 대한 graceful fallback 처리

#### 6) 고도화 및 확장 📋

- [ ] LangGraph 기반 멀티툴 조합, 복합 질의 처리
- [x] 실시간/비동기 처리 등 고도화
- [ ] LangGraph 기반 워크플로우 시각화 및 관리 도구 개발

---

이후 LangGraph 관련 코드는 `app/langgraph/` 폴더에 집중 관리하며, 기존 서비스와의 통합 및 확장성을 고려해 개발을 진행할 예정입니다.

## 1. 프로젝트 구조

```
seobi-backend/
│
├── app/
│   ├── __init__.py                 # Flask 앱 초기화
│   ├── dao/                        # 데이터 접근 객체(DAO)
│   ├── langgraph/                  # LangGraph AI 에이전트 시스템
│   │   ├── agent/                  # 메인 에이전트
│   │   ├── background/             # 백그라운드 업무 처리
│   │   ├── cleanup/                # 대화 정리 및 분석
│   │   ├── parsing_agent/          # 자연어 파싱 에이전트
│   │   ├── general_agent/          # 일반 에이전트
│   │   ├── insight/                # 인사이트 생성
│   │   └── tools/                  # 도구 함수들
│   │       ├── search.py           # 검색 도구
│   │       ├── weather.py          # 날씨 도구
│   │       ├── schedule.py         # 일정 도구
│   │       └── memory.py           # 메모리 도구
│   ├── models/                     # 데이터베이스 모델
│   ├── routes/                     # API 엔드포인트
│   │   └── debug/                  # 디버그용 엔드포인트
│   ├── schemas/                    # API 스키마 정의
│   ├── services/                   # 비즈니스 로직
│   │   └── reports/                # 리포트 관련 서비스
│   └── utils/                      # 유틸리티 함수
├── tests/                          # 테스트 코드
├── migrations/                     # Alembic 마이그레이션
├── config.py                       # 환경 설정
├── main.py                         # 애플리케이션 진입점
├── requirements.txt                # 의존성 목록
├── pyproject.toml                  # 프로젝트 메타데이터
├── uv.lock                         # uv 패키지 매니저 lock 파일
├── pytest.ini                      # pytest 설정
├── .python-version                 # Python 버전
└── .gitignore                      # Git 무시 파일
```

## 2. 주요 기능

### 2.1 사용자 관리
- 사용자 등록, 조회, 수정, 삭제 (CRUD)
- JWT 기반 인증 시스템
- Google OAuth 연동

### 2.2 세션 관리
- 대화 세션 생성 및 관리
- 세션별 대화 이력 저장
- 세션 상태 추적 (진행중/완료)

### 2.3 메시지 관리
- 실시간 메시지 스트리밍
- 메시지 벡터 임베딩 (pgvector)
- 키워드 추출 및 메타데이터 관리

### 2.4 AI 에이전트 시스템
- LangGraph 기반 대화 에이전트
- 도구 호출 및 결과 처리
- 대화 요약 및 정리

### 2.5 Model Context Protocol(MCP) 도구 시스템
- **검색 도구**: 웹 검색, Google 뉴스
- **일정 관리**: 일정 생성, 조회, 수정
- **날씨 정보**: 일일 날씨 예보
- **메모리 시스템**: 유사 메시지 검색, 인사이트 아티클
- **Model Context Protocol 서버 등록**: 외부 도구 연동

### 2.6 자동 업무 시스템
- 백그라운드 업무 실행
- 업무 단계별 의존성 관리
- 업무 상태 추적 및 결과 저장

### 2.7 인사이트 시스템
- 대화 내용 기반 인사이트 생성
- 키워드 및 관심사 연동
- TTS 스크립트 생성

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
![Model Context Protocol](https://img.shields.io/badge/Model%20Context%20Protocol-FF6B6B.svg?style=for-the-badge&logo=model-context-protocol&logoColor=white)
![Redis](https://img.shields.io/badge/Redis-DC382D.svg?style=for-the-badge&logo=Redis&logoColor=white)
![pgvector](https://img.shields.io/badge/pgvector-336791.svg?style=for-the-badge&logo=postgresql&logoColor=white)

### Dev & Ops

![UV](https://img.shields.io/badge/uv-DE5FE9.svg?style=for-the-badge&logo=uv&logoColor=white)
![Github-Actions](https://img.shields.io/badge/GitHub%20Actions-2088FF.svg?style=for-the-badge&logo=GitHub-Actions&logoColor=white)
![Swagger](https://img.shields.io/badge/Swagger-85EA2D.svg?style=for-the-badge&logo=Swagger&logoColor=black)
![OpenSSL](https://img.shields.io/badge/OpenSSL-721412.svg?style=for-the-badge&logo=OpenSSL&logoColor=white)
![Postgresql](https://img.shields.io/badge/PostgreSQL-4169E1.svg?style=for-the-badge&logo=PostgreSQL&logoColor=white)
![Pytest](https://img.shields.io/badge/Pytest-0A9EDC.svg?style=for-the-badge&logo=Pytest&logoColor=white)
![Coverage](https://img.shields.io/badge/Coverage-0070C0.svg?style=for-the-badge&logo=Coverage&logoColor=white)

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
