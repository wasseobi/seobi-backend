from langchain_core.tools import BaseTool, tool
from langchain_community.tools.tavily_search import TavilySearchResults
from typing import Dict, Union, Any
import os
import json
import logging
from flask import request, g

@tool
def search_web(query: str) -> str:
    """웹에서 정보를 검색하는 도구입니다. 날씨, 뉴스, 정보 등을 검색할 수 있습니다."""
    print(f"\n=== Search Web Debug ===")
    print(f"Query: {query}")
    try:
        search = TavilySearchResults(api_key=os.environ["TAVILY_API_KEY"])
        results = search.invoke(query)
        return str(results)
    except Exception as e:
        print(f"Search error: {type(e)} - {str(e)}")
        return f"검색 중 오류 발생: {str(e)}"

@tool
def calculator(expression: str) -> Union[float, str]:
    """수식을 계산하는 도구입니다. 예: '2 + 2', '5 * 3' 등의 수식을 계산할 수 있습니다."""
    print(f"\n=== Calculator Debug ===")
    print(f"Expression: {expression}")
    try:
        result = float(eval(expression, {"__builtins__": None}, {}))
        print(f"Result: {result}")
        return result
    except Exception as e:
        error_msg = f"계산 오류: {str(e)}"
        print(f"Error: {error_msg}")
        return error_msg

@tool
def search_similar_messages(query: str, top_k: int = 5) -> str:
    """
    현재 세션의 user_id로 해당 사용자의 모든 메시지 벡터 중 쿼리와 가장 유사한 메시지 top-N을 반환합니다.
    Args:
        query (str): 검색 쿼리(자연어)
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
    logger = logging.getLogger(__name__)
    logger.debug(f"[TOOL 호출] search_similar_messages(user_id={user_id}, query={query}, top_k={top_k})")
    from app.services.message_service import MessageService
    message_service = MessageService()
    results = message_service.search_similar_messages(user_id, query, top_k)
    return json.dumps(results, ensure_ascii=False)

tools = [search_web, calculator, search_similar_messages]