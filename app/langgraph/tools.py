from langchain_core.tools import Tool
from langchain_community.tools.tavily_search import TavilySearchResults
from typing import Dict, Union, Any
import os
import json

def search_web(query: str) -> str:
    """Tavily 검색 도구를 사용하여 웹에서 정보를 검색합니다."""
    print(f"\n=== Search Web Debug ===")
    print(f"Query: {query}")
    try:
        search = TavilySearchResults(api_key=os.environ["TAVILY_API_KEY"])
        results = search.invoke(query)
        print(f"Search results: {results}")
        return str(results)
    except Exception as e:
        print(f"Search error: {type(e)} - {str(e)}")
        return f"검색 중 오류 발생: {str(e)}"

def calculator(expression: str) -> Union[float, str]:
    """안전한 환경에서 수학 수식을 계산합니다."""
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

# Tool 객체 생성
search_web_tool = Tool(
    name="search_web",
    func=search_web,
    description="웹에서 정보를 검색하는 도구입니다"
)

calculator_tool = Tool(
    name="calculator",
    func=calculator,
    description="수학 수식을 계산하는 도구입니다"
)
