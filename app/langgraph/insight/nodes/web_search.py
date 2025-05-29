def search_web_for_keywords(context):
    from app.langgraph.tools import google_news, google_search
    import logging
    insight_graph_logger = logging.getLogger("insight_graph_debug")
    """
    각 키워드별로 최신 뉴스(tbs='qdr:w')와 과거 뉴스(tbs='qdr:m6')를 각각 google_news로 검색
    context['keywords'] 필요, context['recent_news'], context['past_news']에 결과 저장
    추가: 모든 뉴스 링크를 context['source']에 리스트로 저장
    """
    keywords = context.get('keywords', [])
    recent_news = {}
    past_news = {}
    all_links = []
    for keyword in keywords:
        try:
            recent = google_news.run(keyword, num_results=5, tbs="qdr:w")
            past = google_news.run(keyword, num_results=5, tbs="qdr:m6")
            # 반환값 구조 로그
            insight_graph_logger.debug(f"[WEB_SEARCH] recent({keyword})={recent}")
            insight_graph_logger.debug(f"[WEB_SEARCH] past({keyword})={past}")
            # news 필드에서 link만 추출
            if isinstance(recent, dict) and 'news' in recent:
                all_links.extend([item.get('link') for item in recent['news'] if item.get('link')])
                recent_news[keyword] = recent['news']
            else:
                recent_news[keyword] = recent
            if isinstance(past, dict) and 'news' in past:
                all_links.extend([item.get('link') for item in past['news'] if item.get('link')])
                past_news[keyword] = past['news']
            else:
                past_news[keyword] = past
        except Exception as e:
            recent_news[keyword] = [{"error": str(e)}]
            past_news[keyword] = [{"error": str(e)}]
    # source 누적 방식(중복 제거)
    prev_links = set(context.get('source', []))
    all_links = prev_links.union(all_links)
    context['recent_news'] = recent_news
    context['past_news'] = past_news
    context['source'] = list(all_links)
    insight_graph_logger.debug(f"[WEB_SEARCH] context['source']={context['source']}")
    return context
