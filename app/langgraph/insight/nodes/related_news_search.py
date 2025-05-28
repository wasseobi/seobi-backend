from app.langgraph.tools import google_search


def search_related_news(context):
    """
    연결 키워드로 추가 뉴스 검색 (GoogleSerperAPIWrapper 등)
    context['related_keywords'] 필요, context['related_news']에 결과 저장
    """
    related_keywords = context.get('related_keywords', [])
    related_news = {}
    for keyword in related_keywords:
        try:
            results = google_search(keyword, num_results=5)
            related_news[keyword] = results
        except Exception as e:
            related_news[keyword] = [{"error": str(e)}]
    context['related_news'] = related_news
    return context
