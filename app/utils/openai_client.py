import os
from openai import AzureOpenAI
from langchain.chat_models import init_chat_model
from langchain_core.tools import BaseTool, tool
from typing import List
from app.utils.app_config import get_openai_config

def init_langchain_llm(tools: List[BaseTool] = None):
    """Initialize LangChain LLM with Azure OpenAI configuration"""
    config = get_openai_config()
    deployment_name = config['deployment_name']
    llm = init_chat_model(
        model=deployment_name,
        model_provider="azure_openai",
        azure_deployment=deployment_name,
        azure_endpoint=config['endpoint'],
        api_key=config['api_key'],
        api_version=config['api_version'],
        timeout=60,
        streaming=True
    )

    if tools:
        return llm.bind_tools(tools)
    return llm

def _get_openai_client():
    """Get configured Azure OpenAI client"""
    config = get_openai_config()
    client = AzureOpenAI(
        api_key=config['api_key'],
        api_version=config['api_version'],
        azure_endpoint=config['endpoint']
    )
    return client

def get_completion(messages, max_completion_tokens=2000):
    """Generate chat completion using Azure OpenAI."""
    client = _get_openai_client()
    try:
        config = get_openai_config()
        response = client.chat.completions.create(
            model=config['deployment_name'],
            messages=messages,
            max_completion_tokens=max_completion_tokens
        )

        return response.choices[0].message.content
    except Exception as e:
        raise RuntimeError(f"Error calling OpenAI API: {str(e)}")

def get_embedding(text: str) -> list[float]:
    """Generate embedding vector using Azure OpenAI."""
    client = _get_openai_client()
    try:
        config = get_openai_config()
        response = client.embeddings.create(
            input=text,
            model=config['embedding_deployment_name']
        )
        return response.data[0].embedding
    except Exception as e:
        raise RuntimeError(f"Error calling OpenAI Embedding API: {str(e)}")
