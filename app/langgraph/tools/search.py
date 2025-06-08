from langchain_core.tools import tool
from langchain_community.tools.tavily_search import TavilySearchResults
from langchain_google_community import GoogleSearchAPIWrapper
from langchain_community.utilities import GoogleSerperAPIWrapper
from typing import Dict, List
import os
from bs4 import BeautifulSoup
import os
import requests


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
def google_search_expansion(query: str, num_results: int = 3) -> List[Dict[str, str]]:
    """Google 검색을 수행하고, 각 결과의 스니펫을 HTML 본문에서 확장합니다.

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
        raw_results = search.results(query, num_results=num_results)

        enhanced_results = []
        for result in raw_results:
            snippet = result.get("snippet", "")
            url = result.get("link", "")
            try:
                response = requests.get(url, timeout=3)
                soup = BeautifulSoup(response.text, "html.parser")
                page_text = soup.get_text(separator=" ", strip=True)
                extended_snippet = page_text[:500]  # 최대 500자까지 본문에서 추출
                snippet += f"\n\n[본문 발췌] {extended_snippet}"
            except Exception as e:
                snippet += f"\n\n[본문 발췌 실패: {e}]"
            enhanced_results.append({
                "title": result.get("title", ""),
                "link": url,
                "snippet": snippet
            })

        return enhanced_results

    except Exception as e:
        return [{"error": f"예외 발생: {str(e)}"}]


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
