"""
인사이트 생성용 LangGraph 전체 워크플로우 정의
"""
from langgraph.graph import Graph, END, START
from .nodes.keyword_extractor import extract_top_keywords
from .nodes.web_search import search_web_for_keywords
from .nodes.document_loader import load_documents
from .nodes.relation_analyzer import analyze_relations
from .nodes.related_news_search import search_related_news
from .nodes.insight_generator import generate_insight
from .nodes.title_tags_generator import generate_title_tags
from .nodes.tts_script_generator import generate_tts_script

# 노드 실행 래퍼
def log_node(node_name, func):
    def wrapper(context):
        result = func(context)
        return result
    return wrapper

def build_insight_graph():
    graph = Graph()

    def start_node(context):
        # user_id만 있는 context로 시작 → 키워드 추출 결과를 context에 추가
        user_id = context.get('user_id')
        keywords_info = extract_top_keywords(user_id)
        context.update(keywords_info)
        return context

    graph.add_node("extract_keywords", log_node("extract_keywords", start_node))
    graph.add_node("search_web", log_node("search_web", search_web_for_keywords))
    graph.add_node("load_docs", log_node("load_docs", load_documents))
    graph.add_node("analyze_relations", log_node("analyze_relations", analyze_relations))
    graph.add_node("search_related_news", log_node("search_related_news", search_related_news))
    graph.add_node("generate_insight", log_node("generate_insight", generate_insight))
    graph.add_node("generate_title_tags", log_node("generate_title_tags", generate_title_tags))
    graph.add_node("generate_tts_script", log_node("generate_tts_script", generate_tts_script))

    # 엣지 연결: 1 → 2 → 3 → 4 → (조건부) 2 or 5 → 6 → 7 → 8 → END
    graph.add_edge(START, "extract_keywords")
    graph.add_edge("extract_keywords", "search_web")
    graph.add_edge("search_web", "load_docs")
    graph.add_edge("load_docs", "analyze_relations")

    def analyze_conditional(context):
        if context.get('use_news_fallback'):
            return "search_web"
        elif context.get('related_keywords'):
            return "search_related_news"
        else:
            return "generate_insight"

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
    graph.add_edge("generate_insight", "generate_title_tags")
    graph.add_edge("generate_title_tags", "generate_tts_script")
    graph.add_edge("generate_tts_script", END)

    return graph
