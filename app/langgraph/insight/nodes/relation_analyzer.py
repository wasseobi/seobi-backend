from app.utils.openai_client import get_openai_client, get_completion
from app.utils.prompt.insight_prompts import INSIGHT_ANALYSIS_PROMPT, INSIGHT_COMPARE_PROMPT

def analyze_relations(context):
    """
    최근 뉴스와 과거 뉴스 각각 요약, 두 요약의 차이점/연결점/시사점 LLM에 요청
    context['recent_news_docs'], context['past_news_docs'] 필요
    context['recent_summary'], context['past_summary'], context['insight_analysis']에 결과 저장
    """
    client = get_openai_client()
    # 1. 최근 뉴스 요약
    recent_text = "\n".join([getattr(doc, 'page_content', str(doc)) for doc in context.get('recent_news_docs', [])])
    messages = [
        {"role": "system", "content": "아래 뉴스 본문을 요약해줘."},
        {"role": "user", "content": recent_text}
    ]
    recent_summary = get_completion(client, messages)
    context['recent_summary'] = recent_summary
    # 2. 과거 뉴스 요약
    past_text = "\n".join([getattr(doc, 'page_content', str(doc)) for doc in context.get('past_news_docs', [])])
    messages = [
        {"role": "system", "content": "아래 뉴스 본문을 요약해줘."},
        {"role": "user", "content": past_text}
    ]
    past_summary = get_completion(client, messages)
    context['past_summary'] = past_summary
    # 3. 두 요약의 차이점/연결점/시사점 분석
    compare_prompt = INSIGHT_COMPARE_PROMPT.format(
        recent_summary=recent_summary,
        past_summary=past_summary
    )
    messages = [
        {"role": "system", "content": "아래 두 요약의 차이점, 연결점, 시사점을 분석해줘."},
        {"role": "user", "content": compare_prompt}
    ]
    insight_analysis = get_completion(client, messages)
    context['insight_analysis'] = insight_analysis
    # 기존 연결고리/related_keywords 추출 등은 필요시 추가
    return context
