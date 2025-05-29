"""Conversation summarizer node implementation."""
from datetime import datetime
import json
from langchain.chat_models import ChatOpenAI
from langchain.prompts import ChatPromptTemplate

from ..state import BackgroundState, SummaryResults, SummaryMetadata
from ..prompts.summarizer import SUMMARY_PROMPT


async def conversation_summarizer_node(state: BackgroundState) -> BackgroundState:
    """대화 내용을 요약하는 노드.
    
    Args:
        state: 현재 처리 상태
        
    Returns:
        BackgroundState: 요약 결과가 포함된 업데이트된 상태
    """
    try:
        # 분석 결과 확인
        if not state.get("analysis_results"):
            return {
                **state,
                "error": "분석 결과가 없습니다",
                "next_step": "end"
            }
            
        analysis_results = state["analysis_results"]
        processed_data = state.get("processed_data", {})
        messages = processed_data.get("messages", [])
        metadata = processed_data.get("metadata", {})
        
        # LLM 초기화
        llm = ChatOpenAI(
            temperature=0.1,
            model_name="gpt-4"
        )
        
        # 요약 프롬프트 설정
        summary_prompt = ChatPromptTemplate.from_messages([
            ("system", """당신은 전문적인 대화 요약가입니다. 다음 대화 분석 결과를 바탕으로 요약을 작성해주세요:

분석 결과:
{analysis_results}

추가 컨텍스트:
- 총 메시지 수: {message_count}
- 시간 범위: {time_span}
- 참여자: {participants}

다음 내용을 포함한 요약을 작성해주세요:
1. 대화의 간단한 개요
2. 주요 결정사항이나 결론
3. 중요한 액션 아이템이나 다음 단계
4. 주목할 만한 우려사항이나 하이라이트

응답은 다음 키를 가진 JSON 객체 형식으로 작성해주세요:
- overview: 전체 대화의 간단한 요약
- key_decisions: 중요한 결정사항이나 결론 목록
- action_items: 구체적인 액션 아이템이나 다음 단계 목록
- highlights: 주목할 만한 포인트나 우려사항 목록
- confidence: 요약 신뢰도 (0에서 1 사이의 실수)
"""),
            ("user", "{conversation}")
        ])
        
        # 시간 범위 계산
        timestamps = [datetime.fromisoformat(msg["timestamp"]) for msg in messages if msg.get("timestamp")]
        time_span = "알 수 없음"
        if timestamps:
            start_time = min(timestamps)
            end_time = max(timestamps)
            time_span = f"{start_time.strftime('%Y-%m-%d %H:%M')} ~ {end_time.strftime('%Y-%m-%d %H:%M')}"
        
        # 요약 실행
        chain = summary_prompt | llm
        result = await chain.ainvoke({
            "analysis_results": json.dumps(analysis_results.dict(), ensure_ascii=False, indent=2),
            "message_count": len(messages),
            "time_span": time_span,
            "participants": metadata.get("participants", "알 수 없음")
        })
        
        try:
            summary_data = json.loads(result.content)
        except json.JSONDecodeError:
            # JSON 파싱 실패 시 기본값 사용
            summary_data = {
                "overview": "요약 생성 실패",
                "key_decisions": [],
                "action_items": [],
                "highlights": [],
                "confidence": 0.0
            }
        
        # 요약 메타데이터 추가
        summary_metadata = SummaryMetadata(
            summarized_at=datetime.now().isoformat(),
            model_used="gpt-4",
            confidence=summary_data.get("confidence", 0.0),
            version="1.0"
        )
        
        # 요약 결과 생성
        summary_results = SummaryResults(
            overview=summary_data.get("overview", ""),
            key_decisions=summary_data.get("key_decisions", []),
            action_items=summary_data.get("action_items", []),
            highlights=summary_data.get("highlights", []),
            metadata=summary_metadata
        )
        
        # 상태 업데이트
        return {
            **state,
            "summary_results": summary_results,
            "next_step": "end"
        }
        
    except Exception as e:
        return {
            **state,
            "error": f"요약 중 오류 발생: {str(e)}",
            "next_step": "end"
        } 