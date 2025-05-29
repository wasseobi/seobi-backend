from app.utils.openai_client import get_openai_client, get_completion

def generate_tts_script(context):
    """
    인사이트 기사 본문(context['insight'] 또는 context['text'])를 입력으로 TTS용 script를 LLM으로 생성
    결과를 context['script']에 저장
    """
    content = context.get('insight') or context.get('text')
    if not content:
        return context
    prompt = (
        "아래의 칼럼을 자연스럽게 읽어줄 수 있는 TTS 스크립트로 변환해줘. "
        "구어체, 청취자 친화적으로 작성해줘.\n"
        "[기사 본문]\n" + content
    )
    client = get_openai_client()
    messages = [
        {"role": "system", "content": "TTS 스크립트를 생성해줘."},
        {"role": "user", "content": prompt}
    ]
    response = get_completion(client, messages)
    context['script'] = response
    context['text'] = content
    # source가 없으면 빈 리스트로 보정
    if 'source' not in context or context['source'] is None:
        context['source'] = []
    # 최종 반환 형태: {text, script, title, tags, source, ...}
    return context
