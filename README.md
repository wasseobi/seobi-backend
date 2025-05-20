# seobi-db 리팩토링 구조 및 사용법

## 1. 폴더 구조

```
seobi-db/
│
├── app/
│   ├── __init__.py         # Flask 앱 생성 및 확장자 초기화
│   ├── routes/             # 라우트(엔드포인트) 모음
│   │   ├── __init__.py
│   │   ├── user.py         # User CRUD
│   │   ├── session.py      # Session CRUD
│   │   ├── message.py      # Message CRUD
│   │   ├── mcp_server.py   # MCPServer CRUD
│   │   └── mcp_server_activation.py # ActiveMCPServer CRUD
│   └── models/             # 모델(테이블) 정의 (기존 models 폴더 활용)
│
├── migrations/             # DB 마이그레이션 폴더
├── main.py                 # 앱 실행만 담당
├── config.py               # 환경설정
├── create_app_structure.py # 폴더/파일 자동 생성 스크립트
├── .env
└── ...
```

## 2. 자동화 스크립트 사용법

```bash
python create_app_structure.py
```
- 위 명령어로 리팩토링 구조에 필요한 폴더/파일이 자동 생성됩니다.

## 3. 주요 파일 설명
- `main.py`: 앱 실행만 담당
- `app/__init__.py`: Flask 앱, DB, Blueprint 등록
- `app/routes/`: 테이블별 CRUD 라우트
- `app/models/`: 테이블 모델 정의 (기존 models 폴더 활용)
- `config.py`: DB 등 환경설정

## 4. CRUD 라우트 구조
- 각 테이블별로 `app/routes/테이블명.py`에 Blueprint로 CRUD API 구현
- 예시: `/users`, `/sessions`, `/messages`, `/mcp_servers`, `/mcp_server_activations`

## 5. 의존성 설치

```bash
uv sync
```

## 6. 서버 실행

```bash
python main.py
```
