"""LangChain LLM 설정."""
import os
from dotenv import load_dotenv
from langchain.chat_models import init_chat_model
from langchain_core.tools import BaseTool, tool
from typing import List

# .env 파일 로드
load_dotenv(override=True)

# Azure OpenAI 설정
deployment_name = os.getenv("AZURE_OPENAI_DEPLOYMENT_NAME")
llm = init_chat_model(
    model=deployment_name,
    model_provider="azure_openai",
    azure_deployment=deployment_name,
    azure_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT"),
    api_key=os.getenv("AZURE_OPENAI_API_KEY"),
    api_version=os.getenv("AZURE_OPENAI_API_VERSION"),
    temperature=0.5,
    timeout=60
)

# 도구 가져오기
from .tools import tools

# 도구가 바인딩된 모델
model = llm.bind_tools(tools)
