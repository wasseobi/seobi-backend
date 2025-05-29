from app.utils.openai_client import get_openai_client, get_completion

def generate_title_tags(context):
    """
    인사이트 기사 본문(context['insight'] 또는 context['text'])를 입력으로 title, tags를 LLM으로 생성
    결과를 context['title'], context['tags']에 저장
    """
    content = context.get('insight') or context.get('text')
    if not content:
        return context
    prompt = (
        "아래 기사 본문을 읽고, 반드시 JSON 형태로만 응답해. 예시: {\"title\": \"...\", \"tags\": [\"...\", ...]}\n"
        "[기사 본문]\n" + content
    )
    client = get_openai_client()
    messages = [
        {"role": "system", "content": "기사 제목과 태그를 반드시 JSON 형태로만 생성해줘. 예시: {\"title\": \"...\", \"tags\": [\"...\", ...]}"},
        {"role": "user", "content": prompt}
    ]
    response = get_completion(client, messages)
    try:
        import json
        parsed = json.loads(response)
        context['title'] = parsed.get('title', '')
        context['tags'] = parsed.get('tags', [])
    except Exception:
        context['title'] = response
        context['tags'] = []
    return context
