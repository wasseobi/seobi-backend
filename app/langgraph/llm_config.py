import os
from dotenv import load_dotenv
from langchain_openai import AzureChatOpenAI
from langchain_core.tools import BaseTool, tool
from typing import List

# .env 파일 로드
load_dotenv(override=True)

# Azure OpenAI 설정
llm = AzureChatOpenAI(
    azure_deployment=os.getenv("AZURE_OPENAI_DEPLOYMENT_NAME"),
    openai_api_key=os.getenv("AZURE_OPENAI_API_KEY"),
    azure_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT"),
    api_version=os.getenv("AZURE_OPENAI_API_VERSION"),
    temperature=0.5,
)

# 도구 정의
@tool
def search_web(query: str) -> str:
    """웹에서 정보를 검색하는 도구입니다. 날씨, 뉴스, 정보 등을 검색할 수 있습니다."""
    from .tools import search_web_tool
    return search_web_tool.invoke({"query": query})

@tool
def calculator(expression: str) -> str:
    """수식을 계산하는 도구입니다. 예: '2 + 2', '5 * 3' 등의 수식을 계산할 수 있습니다."""
    from .tools import calculator_tool
    return calculator_tool.invoke({"expression": expression})

# 도구 목록 생성
tools = [search_web, calculator]

# LLM에 도구 바인딩 (function calling 설정 포함)
llm = llm.bind(
    functions=[{
        "name": tool.name,
        "description": tool.description,
        "parameters": {
            "type": "object",
            "properties": {
                "query" if tool.name == "search_web" else "expression": {
                    "type": "string",
                    "description": "검색할 내용" if tool.name == "search_web" else "계산할 수식"
                }
            },
            "required": ["query" if tool.name == "search_web" else "expression"]
        }
    } for tool in tools]
)

# 도구가 바인딩된 모델
model = llm.bind_tools(tools)
