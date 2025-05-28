from app.utils.openai_client import get_openai_client, get_completion
from app.utils.prompt.insight_prompts import INSIGHT_ANALYSIS_PROMPT

def generate_insight(context):
    """
    모든 문서, 키워드, 연결 키워드, 관계 구조를 LLM에 입력해 인사이트 생성
    context['documents'], context['relations'], context['related_news'] 등 필요
    context['insight']에 결과 저장
    """
    keywords = context.get('keywords', [])
    documents = context.get('documents', [])
    related_news = context.get('related_news', {})
    relations = context.get('relations', "")
    document_text = "\n".join([getattr(doc, 'page_content', str(doc)) for doc in documents])
    related_news_text = "\n".join([str(item) for sublist in related_news.values() for item in sublist])
    prompt = INSIGHT_ANALYSIS_PROMPT.format(
        keywords=", ".join(keywords),
        context=document_text + "\n" + related_news_text + "\n" + str(relations)
    )
    client = get_openai_client()
    messages = [
        {"role": "system", "content": "아래 프롬프트에 따라 인사이트를 생성해줘."},
        {"role": "user", "content": prompt}
    ]
    response = get_completion(client, messages)
    context['insight'] = response
    return context
