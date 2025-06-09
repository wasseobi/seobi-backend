def search_related_news(context):
    from app.langgraph.tools import google_news
    from app.utils.openai_client import get_completion
    import re
    """
    연결 키워드로 추가 뉴스 검색 및 요약
    context['related_keywords'] 필요, context['related_news']에 결과 저장
    추가: 관련 뉴스의 링크도 context['source']에 누적 저장
    """
    def clean_text(text):
        # 연속된 공백 문자를 하나의 공백으로
        text = re.sub(r'\s+', ' ', text)
        # 연속된 줄바꿈을 하나의 줄바꿈으로
        text = re.sub(r'\n\s*\n', '\n', text)
        # HTML 태그 제거
        text = re.sub(r'<[^>]+>', '', text)
        # 특수문자 정리 (&nbsp; 등)
        text = re.sub(r'&\w+;', ' ', text)
        # 양쪽 공백 제거
        return text.strip()
        
    def summarize_news(news_items):
        """뉴스 아이템 목록을 요약"""
        # 뉴스 텍스트 결합 및 정리
        news_text = "\n\n".join([
            f"제목: {clean_text(item.get('title', ''))}\n"
            f"내용: {clean_text(item.get('snippet', ''))}"
            for item in news_items
        ])
        
        # 요약 생성
        messages = [
            {"role": "system", "content": "아래 뉴스들을 간단히 요약해주세요."},
            {"role": "user", "content": news_text}
        ]
        summary = get_completion(messages)
        return clean_text(summary)

    related_keywords = context.get('related_keywords', [])
    related_news = {}
    new_links = []
    
    for keyword in related_keywords:
        try:
            results = google_news.run(keyword, num_results=3, tbs=None)
            if isinstance(results, dict) and 'news' in results:
                news_items = results['news']
                # 각 뉴스 아이템 정리
                clean_news_items = []
                for item in news_items:
                    clean_item = {
                        'title': clean_text(item.get('title', '')),
                        'snippet': clean_text(item.get('snippet', '')),
                        'link': item.get('link', ''),
                        'source': clean_text(item.get('source', '')),
                        'date': item.get('date', '')
                    }
                    clean_news_items.append(clean_item)
                
                # 링크 수집
                new_links.extend([item.get('link') for item in clean_news_items if item.get('link')])
                
                # 뉴스 요약
                if clean_news_items:
                    summary = summarize_news(clean_news_items)
                    related_news[keyword] = {
                        'original': clean_news_items,
                        'summary': summary
                    }
                else:
                    related_news[keyword] = {
                        'original': [],
                        'summary': "관련 뉴스가 없습니다."
                    }
            else:
                related_news[keyword] = {
                    'original': results if isinstance(results, list) else [results],
                    'summary': "뉴스 형식이 올바르지 않습니다."
                }
        except Exception as e:
            related_news[keyword] = {
                'original': [{"error": str(e)}],
                'summary': f"뉴스 검색 중 오류 발생: {str(e)}"
            }
    
    # source 누적 방식(중복 제거)
    prev_links = set(context.get('source', []))
    all_links = prev_links.union(new_links)
    context['related_news'] = related_news
    context['source'] = list(all_links)
    
    return context
