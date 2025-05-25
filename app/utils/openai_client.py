import os
from openai import AzureOpenAI
from flask import current_app
from langchain.chat_models import init_chat_model
from langchain_core.tools import BaseTool, tool
from typing import List

def init_langchain_llm(tools: List[BaseTool] = None):
    """Initialize LangChain LLM with Azure OpenAI configuration"""
    deployment_name = current_app.config['AZURE_OPENAI_DEPLOYMENT_NAME']
    llm = init_chat_model(
        model=deployment_name,
        model_provider="azure_openai",
        azure_deployment=deployment_name,
        azure_endpoint=current_app.config['AZURE_OPENAI_ENDPOINT'],
        api_key=current_app.config['AZURE_OPENAI_API_KEY'],
        api_version=current_app.config['AZURE_OPENAI_API_VERSION'],
        temperature=0.5,
        timeout=60,
        streaming=True
    )

    if tools:
        return llm.bind_tools(tools)
    return llm

def get_openai_client():
    """Get configured Azure OpenAI client"""
    client = AzureOpenAI(
        api_key=current_app.config['AZURE_OPENAI_API_KEY'],
        api_version=current_app.config['AZURE_OPENAI_API_VERSION'],
        azure_endpoint=current_app.config['AZURE_OPENAI_ENDPOINT']
    )
    return client

def get_completion(client, messages, max_completion_tokens=2000):
    """Generate chat completion using Azure OpenAI."""
    try:
        response = client.chat.completions.create(
            model=current_app.config['AZURE_OPENAI_DEPLOYMENT_NAME'],
            messages=messages,
            max_completion_tokens=max_completion_tokens
        )

        return response.choices[0].message.content
    except Exception as e:
        raise RuntimeError(f"Error calling OpenAI API: {str(e)}")

def get_embedding(client, text: str) -> list[float]:
    """Generate embedding vector using Azure OpenAI."""
    try:
        response = client.embeddings.create(
            input=text,
            model=current_app.config['AZURE_OPENAI_EMBEDDING_DEPLOYMENT_NAME']
        )
        return response.data[0].embedding
    except Exception as e:
        raise RuntimeError(f"Error calling OpenAI Embedding API: {str(e)}")
