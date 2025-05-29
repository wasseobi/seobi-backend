def search_related_news(context):
    from app.langgraph.tools import google_news
    """
    연결 키워드로 추가 뉴스 검색 (GoogleSerperAPIWrapper 등)
    context['related_keywords'] 필요, context['related_news']에 결과 저장
    추가: 관련 뉴스의 링크도 context['source']에 누적 저장
    """
    related_keywords = context.get('related_keywords', [])
    related_news = {}
    new_links = []
    for keyword in related_keywords:
        try:
            results = google_news.run(keyword, num_results=5, tbs=None)
            if isinstance(results, dict) and 'news' in results:
                new_links.extend([item.get('link') for item in results['news'] if item.get('link')])
                related_news[keyword] = results['news']
            else:
                related_news[keyword] = results
        except Exception as e:
            related_news[keyword] = [{"error": str(e)}]
    # source 누적 방식(중복 제거)
    prev_links = set(context.get('source', []))
    all_links = prev_links.union(new_links)
    context['related_news'] = related_news
    context['source'] = list(all_links)
    return context
