import os
from openai import AzureOpenAI
from flask import current_app

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
