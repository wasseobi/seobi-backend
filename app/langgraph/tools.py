from langchain_core.tools import BaseTool, tool
from langchain_community.tools.tavily_search import TavilySearchResults
from typing import Dict, Union, Any
import os
import json

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

# 도구 목록
tools = [search_web, calculator]
