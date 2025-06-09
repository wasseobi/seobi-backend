def load_documents(context):
    from langchain_community.document_loaders import WebBaseLoader
    from app.utils.openai_client import get_completion
    import re
    """
    최근 뉴스와 과거 뉴스 각각의 링크에서 본문을 로딩하고 요약
    context['recent_news'], context['past_news'] 필요
    context['recent_news_docs'], context['past_news_docs']에 결과 저장
    """
    def clean_text(text):
        # 연속된 공백 문자를 하나의 공백으로
        text = re.sub(r'\s+', ' ', text)
        # 연속된 줄바꿈을 하나의 줄바꿈으로
        text = re.sub(r'\n\s*\n', '\n', text)
        # 양쪽 공백 제거
        text = text.strip()
        return text
        
    def load_news_docs(news_dict):
        docs = []
        for results in news_dict.values():
            for r in results:
                url = r.get('link')
                if url:
                    try:
                        # 웹 페이지 로딩
                        loader = WebBaseLoader(url)
                        loaded = loader.load()
                        
                        # 본문 내용 정리 및 요약
                        if loaded:
                            # 불필요한 공백과 줄바꿈 정리
                            news_text = clean_text(loaded[0].page_content)
                            messages = [
                                {"role": "system", "content": "아래 뉴스들을 간단히 요약해주세요."},
                                {"role": "user", "content": news_text}
                            ]
                            summary = get_completion(messages)
                            # 요약문도 정리
                            summary = clean_text(summary)
                            loaded[0].page_content = summary
                            docs.extend(loaded)
                    except Exception as e:
                        print(f"Error processing URL {url}: {str(e)}")
                        continue
        return docs

    context['recent_news_docs'] = load_news_docs(context.get('recent_news', {}))
    context['past_news_docs'] = load_news_docs(context.get('past_news', {}))
    
    # 보조 안전장치: source가 없으면 빈 리스트로
    if 'source' not in context or context['source'] is None:
        context['source'] = []
        
    return context
