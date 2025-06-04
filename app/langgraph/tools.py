from langchain_core.tools import BaseTool, tool
from langchain_community.tools.tavily_search import TavilySearchResults
from langchain_google_community import GoogleSearchAPIWrapper
from langchain_community.utilities import GoogleSerperAPIWrapper
from typing import Dict, Union, Any, List
import os
import json
from flask import request, g
from app.services.schedule_service import ScheduleService
import re

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


@tool
def google_search(query: str, num_results: int = 3) -> List[Dict[str, str]]:
    """Google 검색을 수행합니다.

    Args:
        query (str): 검색할 키워드나 문장
        num_results (int, optional): 가져올 결과 수. 기본값 3.

    Returns:
        List[Dict[str, str]]: 검색 결과 리스트. 각 결과는 title, link, snippet을 포함
    """
    try:
        api_key = os.environ['GOOGLE_API_KEY']
        cse_id = os.environ['GOOGLE_CSE_ID']
        if not api_key or not cse_id:
            return [{"error": "환경 변수 GOOGLE_API_KEY 또는 GOOGLE_CSE_ID가 비어 있습니다."}]
        if not isinstance(query, str):
            return [{"error": f"검색어(query)는 문자열이어야 합니다. 현재 타입: {type(query)}"}]
        if not isinstance(num_results, int):
            return [{"error": f"num_results는 int여야 합니다. 현재 타입: {type(num_results)}"}]
        search = GoogleSearchAPIWrapper(
            google_api_key=api_key,
            google_cse_id=cse_id
        )
        results = search.results(query, num_results=num_results)
        return results

    except Exception as e:
        return [{"error": f"검색 중 오류 발생: {str(e)}"}]


@tool
def google_news(query: str, num_results: int = 5, tbs: str = None) -> list:
    """Google Serper API를 활용한 뉴스 검색 도구 (tbs로 기간 지정)"""
    serper_api_key = os.environ['SERPER_API_KEY']
    search = GoogleSerperAPIWrapper(
        serper_api_key=serper_api_key, type="news", tbs=tbs)
    print(
        f"[DEBUG] google_news called with query={query}, num_results={num_results}, tbs={tbs}")
    results = search.results(query, num_results=num_results)
    return results


def clean_text(value):
    if not isinstance(value, str):
        return value
    # 앞뒤의 다양한 특수문자 및 공백 제거 (정규표현식에서 -를 맨 앞/뒤로 이동, 괄호 닫힘 오류 수정)
    return re.sub(r"^[\s'\"`.,*!?\\-]+|[\s'\"`.,*!?\\-]+$", "", value)

@tool
def create_schedule_llm(text: str) -> dict:
    """
    새로운 일정을 추가하는 도구입니다.
    - "일정 추가", "회의 잡아줘", "스케줄 등록" 등 일정/스케줄 관련 명령에만 사용하세요.
    - 과거 대화/기억 검색에는 사용하지 마세요.
    Args:
        text (str): 일정 내용(자연어)
    Returns:
        dict: 생성된 일정 정보 및 안내 메시지
    """
    user_id = None
    if hasattr(g, 'user_id') and g.user_id:
        user_id = g.user_id
    elif request.headers.get('user_id'):
        user_id = request.headers.get('user_id')
    elif request.json and request.json.get('user_id'):
        user_id = request.json.get('user_id')
    if not user_id:
        raise ValueError("user_id를 찾을 수 없습니다. 인증 또는 세션 정보를 확인하세요.")
    import uuid
    try:
        uuid.UUID(user_id)
    except Exception:
        raise ValueError("user_id는 반드시 UUID 형식이어야 합니다.")
    schedule = schedule_service.create_llm(user_id, text)
    # 안내 메시지를 최상단에 배치
    message = f"'{clean_text(schedule.title)}' 일정이 등록되었습니다! 필요시 준비물: {clean_text(schedule.memo) if schedule.memo else '없음'}"
    result = {
        'message': message,
        'id': str(schedule.id),
        'user_id': str(schedule.user_id),
        'title': clean_text(schedule.title),
        'repeat': schedule.repeat,
        'start_at': schedule.start_at.isoformat() if schedule.start_at else None,
        'finish_at': schedule.finish_at.isoformat() if schedule.finish_at else None,
        'location': clean_text(schedule.location),
        'status': schedule.status,
        'memo': clean_text(schedule.memo),
        'linked_service': schedule.linked_service,
        'timestamp': schedule.timestamp.isoformat() if hasattr(schedule, 'timestamp') and schedule.timestamp else None,
    }
    return result

@tool
def get_user_schedules() -> list:
    """
    사용자의 모든 일정을 조회하는 도구입니다.
    - "내 일정 보여줘", "이번주 스케줄 알려줘" 등 일정 조회 명령에만 사용하세요.
    - 과거 대화/기억 검색에는 사용하지 마세요.
    Returns:
        list: 일정 정보 리스트
    """
    user_id = None
    if hasattr(g, 'user_id') and g.user_id:
        user_id = g.user_id
    elif request.headers.get('user_id'):
        user_id = request.headers.get('user_id')
    elif request.json and request.json.get('user_id'):
        user_id = request.json.get('user_id')
    if not user_id:
        raise ValueError("user_id를 찾을 수 없습니다. 인증 또는 세션 정보를 확인하세요.")
    import uuid
    try:
        uuid.UUID(user_id)
    except Exception:
        raise ValueError("user_id는 반드시 UUID 형식이어야 합니다.")
    schedules = schedule_service.get_user_schedules(user_id)
    return [
        {
            'id': str(s.id),
            'user_id': str(s.user_id),
            'title': clean_text(s.title),
            'repeat': s.repeat,
            'start_at': s.start_at.isoformat() if s.start_at else None,
            'finish_at': s.finish_at.isoformat() if s.finish_at else None,
            'location': clean_text(s.location),
            'status': s.status,
            'memo': clean_text(s.memo),
            'linked_service': s.linked_service,
            'timestamp': s.timestamp.isoformat() if hasattr(s, 'timestamp') and s.timestamp else None,
        }
        for s in schedules
    ]

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

schedule_service = ScheduleService()
 
agent_tools = [
    search_web,
    calculator,
    google_search,
    run_insight_graph,
    create_schedule_llm,
    get_user_schedules,
    search_similar_messages
]
                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                          