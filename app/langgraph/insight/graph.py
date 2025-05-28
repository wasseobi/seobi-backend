"""
인사이트 생성용 LangGraph 전체 워크플로우 정의
"""
from langgraph.graph import Graph, END
from .nodes.keyword_extractor import extract_top_keywords
from .nodes.web_search import search_web_for_keywords
from .nodes.document_loader import load_documents
from .nodes.relation_analyzer import analyze_relations
from .nodes.related_news_search import search_related_news
from .nodes.insight_generator import generate_insight

def build_insight_graph():
    graph = Graph()

    def start_node(context):
        # user_id만 있는 context로 시작 → 키워드 추출 결과를 context에 추가
        user_id = context.get('user_id')
        keywords_info = extract_top_keywords(user_id)
        context.update(keywords_info)
        return context

    graph.add_node("extract_keywords", start_node)
    graph.add_node("search_web", search_web_for_keywords)
    graph.add_node("load_docs", load_documents)
    graph.add_node("analyze_relations", analyze_relations)
    graph.add_node("search_related_news", search_related_news)
    graph.add_node("generate_insight", generate_insight)

    # 엣지 연결: 1 → 2 → 3 → 4 → (조건부) 2 or 5 → 6 → END
    graph.add_edge("extract_keywords", "search_web")
    graph.add_edge("search_web", "load_docs")
    graph.add_edge("load_docs", "analyze_relations")

    def analyze_conditional(context):
        # analyze_relations 결과에 따라 분기
        if context.get('use_news_fallback'):
            return "search_web"  # Google Serper 뉴스로 fallback
        elif context.get('related_keywords'):
            return "search_related_news"
        else:
            return "generate_insight"  # 연결고리 없으면 바로 인사이트 생성

    graph.add_conditional_edges(
        source="analyze_relations",
        path=analyze_conditional,
        path_map={
            "search_web": "search_web",
            "search_related_news": "search_related_news",
            "generate_insight": "generate_insight"
        }
    )
    graph.add_edge("search_related_news", "generate_insight")
    graph.add_edge("generate_insight", END)

    return graph
