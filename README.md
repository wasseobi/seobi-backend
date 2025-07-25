# Seobi Backend

Flask 기반의 백엔드 API 서버입니다. PostgreSQL 데이터베이스를 사용하며, SQLAlchemy를 ORM으로 사용합니다.

## 1. 주요 기능

- 사용자 관리 (User CRUD)
- 세션 관리 (Session CRUD)
- 메시지 관리 (Message CRUD)
- MCP 서버 관리 (MCPServer CRUD)
- MCP 서버 활성화 관리 (ActiveMCPServer CRUD)
- 일정 관리 (Schedule CRUD)
- 리포트 관리 (Report CRUD)
- 인사이트 아티클 관리 (InsightArticle CRUD)
- 자동 작업 관리 (AutoTask CRUD)
- 브리핑 관리 (Briefing CRUD)

## 2. 기술 스택

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

## 3. 구현 방식

### 데이터베이스

- PostgreSQL을 사용하여 데이터 저장 및 관리
- SQLAlchemy를 ORM으로 활용하여 데이터베이스 모델 정의 및 쿼리 처리
- Alembic을 사용한 데이터베이스 마이그레이션 관리

### 백엔드 로직

- Flask를 기반으로 API 서버 구현
- Pydantic을 사용하여 데이터 검증 및 스키마 정의
- LangGraph를 활용한 AI/도구 호출 워크플로우 관리
- OpenAI API 연동을 통한 AI 기능 제공

#### MCP (Model Context Protocol)

생성형 AI 모델이 외부 시스템과 연동하거나 특정 컨텍스트(맥락)를 이해하고 활용할 수 있도록 돕는 Anthropic에서 발표한 프로토콜로 주요 기능은은 다음과 같습니다:

- **도구 관리**:
  - 주요 도구:
    - `search_web`: 웹 검색을 수행
    - `google_news`: 뉴스 검색 및 필터링
    - `google_search_expansion`: 검색 키워드 확장
  - 도구 호출은 `call_tool` 및 `run_tool` 노드를 통해 처리됩니다.

#### LangGraph

LangGraph는 AI 기반의 도구 호출 및 워크플로우 관리를 위한 핵심 모듈입니다. 주요 기능과 구현은 다음과 같습니다:

1. **에이전트 아키텍처**
   - `AgentState`: 에이전트의 상태 관리
     - 단기 기억: 메시지 히스토리 관리
     - 장기 기억: 사용자별 중요 정보 저장
     - 도구 상태: 현재 실행 중인 도구 정보 추적
   - `AgentExecutor`: 에이전트 실행 관리
     - 비동기 실행 지원
     - 오류 처리 및 복구
     - MCP 도구 통합

2. **노드 구조**
   - `ModelNode`: LLM 호출 및 응답 생성
     - 컨텍스트 관리
     - 도구 호출 결정
     - 응답 포맷팅
   - `ToolNode`: 도구 실행
     - 동기/비동기 도구 지원
     - 결과 검증
     - 오류 처리
   - `SummarizeNode`: 대화 요약
     - 주기적 요약 생성
     - 컨텍스트 압축
   - `CleanupNode`: 후처리
     - 메모리 정리
     - 상태 최적화

3. **그래프 구조**
   - 조건부 분기 처리:
     ```python
     workflow.add_conditional_edges(
         "agent",
         state_conditional,
         {
             "tool": "tool",
             "cleanup": "cleanup",
         }
     )
     ```
   - 순환 및 반복 처리:
     - 도구 호출 → 결과 평가 → 다음 단계 결정
   - 종료 조건 관리

4. **파싱 에이전트**
   - 자연어 입력 분석
   - 정보 추출 및 검증
   - 필요시 LLM 핸드오프
   - 최대 5회 재시도 로직

5. **백그라운드 처리**
   - 작업 단계별 실행:
     1. 작업 큐 관리
     2. 계획 초기화
     3. 단계 실행
     4. 결과 평가
     5. 작업 완료 처리
   - 실패/재시도 처리
   - 결과 데이터베이스 저장

## 4. 프로젝트 구조

```
seobi-backend/
│
├── app/
│   ├── __init__.py
│   ├── dao/                  # 데이터 접근 객체(DAO) 모음
│   │   ├── auto_task_dao.py
│   │   ├── briefing_dao.py
│   │   ├── insight_article_dao.py
│   │   ├── interest_dao.py
│   │   ├── message_dao.py
│   │   ├── report_dao.py
│   │   ├── schedule_dao.py
│   │   ├── session_dao.py
│   │   └── user_dao.py
│   ├── langgraph/            # LangGraph 연동 및 도구 관련 코드
│   │   ├── agent/
│   │   ├── background/
│   │   ├── cleanup/
│   │   ├── general_agent/
│   │   ├── insight/
│   │   ├── parsing_agent/
│   │   └── tools/
│   ├── models/               # 데이터베이스 모델 정의
│   │   ├── __init__.py
│   │   ├── auto_task.py
│   │   ├── auto_task_step.py
│   │   ├── briefing.py
│   │   ├── db.py
│   │   ├── insight_article.py
│   │   ├── interest.py
│   │   ├── message.py
│   │   ├── mcp_server.py
│   │   ├── mcp_server_activation.py
│   │   ├── report.py
│   │   ├── schedule.py
│   │   ├── session.py
│   │   └── user.py
│   ├── routes/               # API 엔드포인트
│   │   ├── __init__.py
│   │   ├── auth.py
│   │   ├── auto_task.py
│   │   ├── briefing.py
│   │   ├── insight.py
│   │   ├── message.py
│   │   ├── mcp_server.py     # MCP 서버 관련 엔드포인트
│   │   ├── mcp_server_activation.py # MCP 서버 활성화 엔드포인트
│   │   ├── report.py
│   │   ├── schedule.py
│   │   └── session.py
│   ├── schemas/              # Pydantic 등 스키마 정의
│   │   ├── auto_task_schema.py
│   │   ├── background_schema.py
│   │   ├── briefing_schema.py
│   │   ├── insight_schema.py
│   │   ├── message_schema.py
│   │   ├── session_schema.py
│   │   └── user_schema.py
│   ├── services/             # 비즈니스 로직
│   │   ├── auto_task_service.py
│   │   ├── background_service.py
│   │   ├── briefing_service.py
│   │   ├── cleanup_service.py
│   │   ├── insight_article_service.py
│   │   ├── interest_service.py
│   │   ├── message_service.py
│   │   ├── schedule_service.py
│   │   ├── session_service.py
│   │   └── user_service.py
│   └── utils/                # 유틸리티 함수 및 외부 연동
│       ├── agent_state_store.py
│       ├── app_config.py
│       ├── auth_middleware.py
│       ├── auto_task_utils.py
│       ├── json_utils.py
│       ├── map.py
│       ├── openai_client.py
│       ├── summarize_output.py
│       ├── text_cleaner.py
│       ├── time.py
│       └── time_utils.py
│
├── certs/                    # 인증서 등 보안 관련 파일
│   └── certificate.pem
├── logs/                     # 로그 파일
│   └── app.log
├── migrations/               # Alembic 마이그레이션
│   ├── alembic.ini
│   ├── env.py
│   ├── README
│   ├── script.py.mako
│   └── versions/
├── tests/                    # 테스트 코드
│   ├── conftest.py
│   ├── db_setup.py
│   ├── test_db_cleanup.py
│   ├── test_db_setup.py
│   ├── test_dao/
│   └── test_services/
├── config.py                 # 환경 설정
├── main.py                   # 애플리케이션 진입점
├── requirements.txt          # 의존성 목록
├── pyproject.toml            # 프로젝트 메타데이터
└── uv.lock                   # uv 패키지 매니저 lock 파일
```

## 5. 설치 및 실행

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
