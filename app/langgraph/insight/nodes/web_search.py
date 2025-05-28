from app.langgraph.tools import google_search, google_news


def search_web_for_keywords(context):
    """
    각 키워드별로 최신 뉴스(tbs='qdr:w')와 과거 뉴스(tbs='qdr:m6')를 각각 google_news로 검색
    context['keywords'] 필요, context['recent_news'], context['past_news']에 결과 저장
    """
    keywords = context.get('keywords', [])
    recent_news = {}
    past_news = {}
    for keyword in keywords:
        try:
            recent_news[keyword] = google_news(keyword, num_results=5, tbs="qdr:w")
            past_news[keyword] = google_news(keyword, num_results=5, tbs="qdr:m6")
        except Exception as e:
            recent_news[keyword] = [{"error": str(e)}]
            past_news[keyword] = [{"error": str(e)}]
    context['recent_news'] = recent_news
    context['past_news'] = past_news
    return context
