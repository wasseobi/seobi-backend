"""Conversation analyzer node implementation."""
from datetime import datetime
import json
from langchain.chat_models import ChatOpenAI
from langchain.prompts import ChatPromptTemplate

from ..state import BackgroundState, AnalysisResults, AnalysisMetadata
from ..prompts.analyzer import ANALYSIS_PROMPT


async def conversation_analyzer_node(state: BackgroundState) -> BackgroundState:
    """대화 내용을 분석하는 노드.
    
    Args:
        state: 현재 처리 상태
        
    Returns:
        BackgroundState: 분석 결과가 포함된 업데이트된 상태
    """
    try:
        # 처리된 데이터 확인
        if not state.get("processed_data") or not state.get("processed_data", {}).get("messages"):
            return {
                **state,
                "error": "처리된 메시지가 없습니다",
                "next_step": "end"
            }
            
        messages = state["processed_data"]["messages"]
        metadata = state["processed_data"]["metadata"]
        
        # LLM 초기화
        llm = ChatOpenAI(
            temperature=0.1,
            model_name="gpt-4"
        )
        
        # 분석 프롬프트 설정
        analysis_prompt = ChatPromptTemplate.from_messages([
            ("system", """당신은 전문적인 대화 분석가입니다. 다음 대화를 분석하여 다음 정보를 제공해주세요:
            1. 주요 논의 주제
            2. 핵심 포인트
            3. 사용자의 주요 의도
            4. 전체적인 감정
            5. 필요한 후속 조치나 액션 아이템
            
            대화에 대한 추가 컨텍스트:
            - 총 메시지 수: {message_count}
            - 시간 범위: {time_span}
            - 참여자: {participants}
            
            응답은 다음 키를 가진 JSON 객체 형식으로 작성해주세요:
            - topics: 주요 주제 목록
            - key_points: 핵심 포인트 목록
            - user_intent: 주요 의도를 설명하는 문자열
            - sentiment: 감정 상태 (긍정적, 부정적, 중립, 혼합)
            - action_items: 액션 아이템 목록
            - confidence: 분석 신뢰도 (0에서 1 사이의 실수)
            """),
            ("user", "{conversation}")
        ])
        
        # 대화 텍스트 포맷팅
        conversation_text = "\n".join([
            f"{msg['role']}: {msg['content']}"
            for msg in messages
        ])
        
        # 시간 범위 계산
        timestamps = [datetime.fromisoformat(msg["timestamp"]) for msg in messages if msg.get("timestamp")]
        time_span = "알 수 없음"
        if timestamps:
            start_time = min(timestamps)
            end_time = max(timestamps)
            time_span = f"{start_time.strftime('%Y-%m-%d %H:%M')} ~ {end_time.strftime('%Y-%m-%d %H:%M')}"
        
        # 분석 실행
        chain = analysis_prompt | llm
        result = await chain.ainvoke({
            "conversation": conversation_text,
            "message_count": len(messages),
            "time_span": time_span,
            "participants": metadata.get("participants", "알 수 없음")
        })
        
        try:
            analysis_data = json.loads(result.content)
        except json.JSONDecodeError:
            # JSON 파싱 실패 시 기본값 사용
            analysis_data = {
                "topics": [],
                "key_points": [],
                "user_intent": "분석 실패",
                "sentiment": "중립",
                "action_items": [],
                "confidence": 0.0
            }
        
        # 분석 메타데이터 추가
        analysis_metadata = AnalysisMetadata(
            analyzed_at=datetime.now().isoformat(),
            model_used="gpt-4",
            confidence=analysis_data.get("confidence", 0.0),
            version="1.0"
        )
        
        # 분석 결과 생성
        analysis_results = AnalysisResults(
            topics=analysis_data.get("topics", []),
            key_points=analysis_data.get("key_points", []),
            user_intent=analysis_data.get("user_intent", ""),
            sentiment=analysis_data.get("sentiment", "중립"),
            action_items=analysis_data.get("action_items", []),
            metadata=analysis_metadata
        )
        
        # 상태 업데이트
        return {
            **state,
            "analysis_results": analysis_results,
            "next_step": "summarize"
        }
        
    except Exception as e:
        return {
            **state,
            "error": f"분석 중 오류 발생: {str(e)}",
            "next_step": "end"
        } 