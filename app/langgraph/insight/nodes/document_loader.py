from langchain.document_loaders import WebBaseLoader

def load_documents(context):
    """
    최근 뉴스와 과거 뉴스 각각의 링크에서 본문을 로딩
    context['recent_news'], context['past_news'] 필요
    context['recent_news_docs'], context['past_news_docs']에 결과 저장
    """
    def load_news_docs(news_dict):
        docs = []
        for results in news_dict.values():
            for r in results:
                url = r.get('link')
                if url:
                    try:
                        loader = WebBaseLoader(url)
                        loaded = loader.load()
                        docs.extend(loaded)
                    except Exception:
                        continue
        return docs
    context['recent_news_docs'] = load_news_docs(context.get('recent_news', {}))
    context['past_news_docs'] = load_news_docs(context.get('past_news', {}))
    return context
