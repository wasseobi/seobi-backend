from langchain_openai import ChatOpenAI
from app.langgraph.tools import get_tools

# LangGraph agentic 구조에서 재사용할 LLM 인스턴스 (Azure OpenAI)
model_with_tools = ChatOpenAI(
    deployment_name="o4-mini",
    temperature=0
).bind_tools(get_tools())
