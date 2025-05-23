from langchain_openai import ChatOpenAI
from app.langgraph.tools import get_tools
from flask import current_app

# LangGraph agentic 구조에서 재사용할 LLM 인스턴스 (Azure OpenAI)
model_with_tools = ChatOpenAI(
    deployment_name=current_app.config['AZURE_OPENAI_DEPLOYMENT_NAME'],
    temperature=0
).bind_tools(get_tools())
