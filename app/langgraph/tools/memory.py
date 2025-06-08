from langchain_core.tools import tool
import json
from flask import request, g

@tool
def run_insight_graph() -> dict:
    """
    인사이트 그래프를 실행하여 DB에 저장하고, 전체 인사이트 json(dict) 결과를 반환합니다. user_id는 백엔드에서 자동 추출합니다.
    """
    user_id = getattr(g, 'user_id', None) or request.headers.get('user_id')
    if not user_id:
        raise ValueError("user_id를 찾을 수 없습니다. 인증 또는 세션 정보를 확인하세요.")
    from app.services.insight_article_service import InsightArticleService
    service = InsightArticleService()
    article = service.create_article(user_id, type="chat")
    result = {
        "id": str(article.id),
        "title": article.title,
        "content": article.content,
        "tags": article.tags,
        "source": article.source,
        "type": article.type,
        "created_at": article.created_at.isoformat() if article.created_at else None,
        "keywords": article.keywords,
        "interest_ids": article.interest_ids
    }
    return result

@tool
def search_similar_messages(query: str, top_k: int = 5) -> str:
    """
    사용자의 과거 대화(메시지) 중 현재 질문과 관련된 내용을 벡터로 검색합니다.
    - 반드시 "전에 ~라고 했던 거 기억나?", "과거에 ~에 대해 얘기했었지?" 등 과거 대화/기억을 찾을 때만 사용하세요.
    - 일정 추가/조회에는 절대 사용하지 마세요.
    Args:
        query (str): 검색할 내용(자연어)
        top_k (int): 반환할 메시지 개수(기본 5)
    Returns:
        str: 유사 메시지 리스트(JSON 문자열)
    """
    # user_id를 LLM이 넘기지 않아도 request context에서 강제로 가져옴
    user_id = None
    # 1. g.user_id (auth 미들웨어에서 세팅했다면)
    if hasattr(g, 'user_id') and g.user_id:
        user_id = g.user_id
    # 2. 헤더에서 직접 추출
    elif request.headers.get('user_id'):
        user_id = request.headers.get('user_id')
    # 3. json body에서 추출 (fallback)
    elif request.json and request.json.get('user_id'):
        user_id = request.json.get('user_id')
    if not user_id:
        raise ValueError('user_id를 찾을 수 없습니다. 인증 또는 세션 정보를 확인하세요.')
    from app.services.message_service import MessageService
    message_service = MessageService()
    results = message_service.search_similar_messages_pgvector(user_id, query, top_k)
    return json.dumps(results, ensure_ascii=False)