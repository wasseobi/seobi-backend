"""Background processing state type definitions."""
from typing import Dict, List, TypedDict, Union, Optional
from datetime import datetime
from langchain_core.messages import BaseMessage


class ProcessedMessage(TypedDict):
    """정규화된 메시지 데이터"""
    role: str
    content: str
    timestamp: str


class ConversationMetadata(TypedDict):
    """대화 메타데이터"""
    message_count: int
    has_user_messages: bool
    has_assistant_messages: bool
    first_message_time: str
    last_message_time: str
    processed_at: str
    unique_roles: List[str]
    enqueued_at: Optional[str]
    version: Optional[str]


class AnalysisResults(TypedDict):
    """분석 결과"""
    topics: List[str]
    key_points: List[str]
    user_intent: str
    sentiment: str
    action_items: List[str]
    confidence: float


class AnalysisMetadata(TypedDict):
    """분석 메타데이터"""
    analyzed_at: str
    model_used: str
    confidence: float
    analysis_version: str


class SummaryResults(TypedDict):
    """요약 결과"""
    summary: str
    key_decisions: List[str]
    action_items: List[str]
    confidence: float


class BackgroundState(TypedDict):
    """백그라운드 처리 상태"""
    # 기본 정보
    conversation_id: str
    messages: List[ProcessedMessage]
    metadata: ConversationMetadata
    
    # 처리 단계
    next_step: Optional[str]  # 다음 처리 단계 (analyze, summarize, end)
    error: Optional[str]  # 에러 메시지
    
    # 처리 결과
    processed_data: Optional[Dict]  # processor 노드의 처리 결과
    analysis_results: Optional[AnalysisResults]  # analyzer 노드의 분석 결과
    analysis_metadata: Optional[AnalysisMetadata]  # 분석 메타데이터
    summary_results: Optional[SummaryResults]  # summarizer 노드의 요약 결과
    
    # 최종 결과
    final_result: Optional[Dict]  # 최종 처리 결과


def create_initial_state(
    conversation_id: str,
    messages: List[Dict],
    metadata: Optional[Dict] = None
) -> BackgroundState:
    """초기 상태 객체 생성
    
    Args:
        conversation_id: 대화 ID
        messages: 원본 메시지 목록
        metadata: 추가 메타데이터
        
    Returns:
        BackgroundState: 초기화된 상태 객체
    """
    return {
        "conversation_id": conversation_id,
        "messages": messages,
        "metadata": {
            **(metadata or {}),
            "enqueued_at": datetime.now().isoformat(),
            "version": "1.0"
        },
        "next_step": None,
        "error": None,
        "processed_data": None,
        "analysis_results": None,
        "analysis_metadata": None,
        "summary_results": None,
        "final_result": None
    } 