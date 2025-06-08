from langchain_core.tools import tool
import json
from flask import request, g

@tool
def insight_article() -> dict:
    """
    사용자의 가장 최근 아티클을 가져옵니다.
    """
    user_id = getattr(g, 'user_id', None) or request.headers.get('user_id')
    from app.services.insight_article_service import InsightArticleService
    service = InsightArticleService()
    article = service.get_uesr_last_article(user_id)
    return article

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