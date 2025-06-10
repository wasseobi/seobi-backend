from app.dao.message_dao import MessageDAO
from app.models import Session
from app.utils.message.message_context import MessageContext

from app.utils.openai_client import get_embedding, get_completion
from app.utils.message.processor import MessageProcessor
from app.langgraph.agent.executor import create_agent_executor
from app.langgraph.agent.graph import build_graph
from app.utils.agent_state_store import AgentStateStore

from langchain.schema import HumanMessage, AIMessage
from langchain_core.messages import ToolMessage
from typing import List, Dict, Any, Generator
import uuid
from datetime import datetime, timezone
import json
import numpy as np

class MessageService:
    def __init__(self):
        self.message_dao = MessageDAO()
        self.agent_executor = create_agent_executor()
        self.graph = build_graph().compile()
        self.active_contexts: Dict[str, MessageContext] = {}  # 세션별 활성 컨텍스트

    def _serialize_message(self, message: Any) -> Dict[str, Any]:
        """Serialize message data for API response"""
        return {
            'id': str(message.id),
            'session_id': str(message.session_id),
            'user_id': str(message.user_id),
            'content': message.content,
            'role': message.role,
            'timestamp': message.timestamp.isoformat() if message.timestamp else None,
            'vector': message.vector.tolist() if message.vector is not None else None,
            'metadata': message.message_metadata
        }

    def get_all_messages(self) -> List[Dict]:
        """Get all messages"""
        messages = self.message_dao.get_all()
        return [self._serialize_message(msg) for msg in messages]

    def get_message(self, message_id: uuid.UUID) -> Dict:
        """Get a message by ID"""
        message = self.message_dao.get_by_id(message_id)
        if not message:
            raise ValueError('Message not found')
        return self._serialize_message(message)

    def get_session_messages(self, session_id: uuid.UUID) -> List[Dict]:
        """Get all messages in a session"""
        session = Session.query.get(session_id)
        if not session:
            raise ValueError('Session not found')

        messages = self.message_dao.get_all_by_session_id(session_id)
        serialized = [self._serialize_message(msg) for msg in messages]
        return serialized

    def get_conversation_history(self, session_id: uuid.UUID) -> List[Dict[str, str]]:
        """Get conversation history formatted for AI completion"""
        session = Session.query.get(session_id)
        if not session:
            raise ValueError('Session not found')

        messages = self.message_dao.get_all_by_session_id(session_id)
        return [
            {"role": msg.role, "content": msg.content}
            for msg in messages
        ]

    def create_message(self, session_id: uuid.UUID, user_id: uuid.UUID,
                       content: str, role: str, metadata) -> Dict:
        """Create a new message (임베딩 벡터 및 키워드 벡터 포함)""" 

        session = Session.query.get(session_id)
        if not session:
            raise ValueError('Session not found')
        if session.finish_at:
            raise ValueError('Cannot add message to finished session')

        try:
            vector = get_embedding(content)
        except Exception as e:
            vector = None

        # --- 키워드 추출 및 임베딩 추가 ---
        keyword_text = None
        keyword_vector = None
        try:
            # 단일 메시지 content에서 키워드 추출 프롬프트 구성
            messages = [
                {"role": "system", "content": "아래 문장에서 핵심 키워드를 1~3개만 JSON 배열로 뽑아줘. 불필요한 설명 없이 배열만 출력."},
                {"role": "user", "content": content}
            ]
            keywords_response = get_completion(messages)
            print("[디버그] LLM 키워드 추출 응답:", keywords_response)
            keywords = json.loads(keywords_response)
            if isinstance(keywords, list) and keywords:
                keyword_text = ", ".join(keywords)
                # 첫 번째 키워드만 임베딩 (여러 개면 확장 가능)
                keyword_vector = get_embedding(keywords[0])
                print(f"[디버그] 추출 키워드: {keyword_text}, 임베딩: {keyword_vector[:5]}...")
            else:
                print("[디버그] 키워드 추출 결과 없음 또는 형식 오류:", keywords)
        except Exception as e:
            print("[에러] 키워드 추출/임베딩 실패:", e)
            keyword_text = None
            keyword_vector = None

        message = self.message_dao.create(
            session_id, user_id, content, role, vector, metadata,
            keyword_text=keyword_text, keyword_vector=keyword_vector
        )
        return self._serialize_message(message)

    def update_message(self, message_id: uuid.UUID, **kwargs) -> Dict:
        """Update a message"""
        message = self.message_dao.update(message_id, **kwargs)
        if not message:
            raise ValueError('Message not found')
        return self._serialize_message(message)

    def delete_message(self, message_id: uuid.UUID) -> bool:
        """Delete a message"""
        return self.message_dao.delete(message_id)

    def create_langgraph_completion(self, session_id: uuid.UUID, user_id: uuid.UUID,
                                    content: str) -> Generator[Dict, None, None]:
        """LangGraph를 통한 응답 생성."""
        processor = MessageProcessor(str(session_id), str(user_id))
        context = self._get_or_create_context(str(session_id), str(user_id))

        # 메시지 버퍼
        tool_calls_buffer = []  # tool_calls가 있는 AI 메시지
        tool_results_buffer = []  # toolMessage 결과
        final_response_buffer = []  # 최종 AI 응답

        # 1. AgentState 불러오기
        agent_state = AgentStateStore.get(str(user_id))

        agent_state["current_input"] = content
        agent_state["messages"].append(HumanMessage(content=content))

        # 메세지 컨텍스트에 사용자 메시지 추가
        context.add_user_message(content=content)

        # 사용자 메시지 먼저 전송
        yield {
            'type': 'user',
            'content': content,
            'session_id': str(session_id),
            'user_id': str(user_id),
            'metadata': {'timestamp': datetime.now(timezone.utc).isoformat()}
        }

        try:
            print(
                f"[LangGraph] stream start: session_id={session_id}, user_id={user_id}, content={content}")
            for msg_chunk, metadata in self.graph.stream(agent_state, stream_mode="messages"):
                try:
                    chunk_data = None
                    if isinstance(msg_chunk, ToolMessage):
                        # 도구 메시지 처리
                        processed_list = list(
                            processor.process_tool_message(msg_chunk))
                        for processed in processed_list:
                            context.add_tool_result(
                                tool_name=processed.get("metadata", {}).get(
                                    "tool_name", "unknown"),
                                result=processed
                            )
                            if processed.get('content'):
                                tool_results_buffer.append({
                                    'type': 'toolmessage',
                                    'content': processed.get('content', ""),
                                    'metadata': {
                                        **processed.get('metadata', {}),
                                        "tool_response": True
                                    }
                                })

                    elif isinstance(msg_chunk, AIMessage):
                        if hasattr(msg_chunk, "additional_kwargs") and msg_chunk.additional_kwargs.get("tool_calls"):
                            # 도구 호출 처리
                            for tool_call in msg_chunk.additional_kwargs["tool_calls"]:
                                context.add_tool_call_chunk(tool_call)
                                tool_calls_buffer.append({
                                    'type': 'tool_calls',
                                    'tool_calls': [tool_call],
                                    'metadata': {
                                        'tool_call_id': tool_call.get('id', '')
                                    }
                                })

                        elif msg_chunk.content:
                            context.append_assistant_content(msg_chunk.content)
                            final_response_buffer.append({
                                'type': 'chunk',
                                'content': msg_chunk.content,
                                'metadata': metadata
                            })

                    elif isinstance(msg_chunk, dict):
                        if "agent" in msg_chunk:
                            # 에이전트 메시지 처리
                            messages_to_process = msg_chunk["agent"].get(
                                "formatted_messages", [])
                            for processed in processor.process_agent_messages(messages_to_process):
                                if isinstance(processed, str) and processed.startswith("data: "):
                                    processed = json.loads(
                                        processed[len("data: "):])

                                if processed.get("content"):
                                    context.append_assistant_content(
                                        processed["content"])
                                    chunk_data = {
                                        'type': 'chunk',
                                        'content': processed["content"],
                                        'metadata': processed.get("metadata", {})
                                    }
                                    yield chunk_data

                        elif "content" in msg_chunk or "metadata" in msg_chunk:
                            for processed in processor.process_dict_message(msg_chunk):
                                if isinstance(processed, str) and processed.startswith("data: "):
                                    processed = json.loads(
                                        processed[len("data: "):])

                                if processed.get("content"):
                                    context.append_assistant_content(
                                        processed["content"])
                                    chunk_data = {
                                        'type': 'chunk',
                                        'content': processed["content"],
                                        'metadata': processed.get("metadata", metadata)
                                    }
                                    yield chunk_data
                except Exception as e:
                    print(f"[LangGraph] Exception in chunk: {e}")
                    continue

            # tool_calls가 있는 경우에만 순서대로 전송
            if tool_calls_buffer:
                # 2. tool_calls 전송
                for chunk in tool_calls_buffer:
                    yield chunk
                tool_calls_buffer.clear()
                
                # 3. tool 결과 전송 (있는 경우)
                if tool_results_buffer:
                    yield tool_results_buffer
                    tool_results_buffer.clear()

            # 4. 마지막으로 AI 응답 전송
            for chunk in final_response_buffer:
                yield chunk
            final_response_buffer.clear()

            context.finalize_assistant_response()
            self._save_context_messages(context)
            AgentStateStore.set(str(user_id), agent_state)

            # 컨텍스트 초기화
            context.reset()

            yield {
                'type': 'end',
                'context_saved': True
            }

        except Exception as e:
            yield {
                'type': 'error',
                'error': str(e)
            }
            raise
 
    def get_user_messages(self, user_id: uuid.UUID) -> List[Dict]:
        try:
            messages = self.message_dao.get_all_by_user_id(user_id)
            return [self._serialize_message(msg) for msg in messages]
        except Exception as e:
            raise ValueError(f"Failed to get messages for user {user_id}")

    def _get_or_create_context(self, session_id: str, user_id: str) -> MessageContext:
        """세션에 대한 메시지 컨텍스트를 가져오거나 생성합니다."""
        context_key = str(session_id)
        if context_key not in self.active_contexts:
            self.active_contexts[context_key] = MessageContext(
                session_id=str(session_id),
                user_id=str(user_id)
            )
        return self.active_contexts[context_key]

    def _save_context_messages(self, context: MessageContext) -> None:
        """컨텍스트의 모든 메시지를 DB에 저장합니다."""
        try:
            session_id = uuid.UUID(context.session_id)
            user_id = uuid.UUID(context.user_id)
            messages = context.get_messages_for_storage()
            for msg in messages:
                content = msg["content"]
                role = msg["role"]
                metadata = msg.get("metadata")

                self.create_message(
                    session_id=session_id,
                    user_id=user_id,
                    content=content,
                    role=role,
                    metadata=metadata
                )
        except Exception as e:
            print(f"[Error] Failed to save context messages: {e}")
            raise ValueError(f"Failed to save messages: {str(e)}")

    def search_similar_messages_pgvector(self, user_id: str, query: str, top_k: int = 5) -> list[dict]:
        """
        [PGVECTOR] user_id의 메시지 중 쿼리 임베딩과 가장 유사한 top_k 메시지 반환 (DB에서 벡터 연산)
        """
        query_vec = np.array(get_embedding(query))

        messages = self.message_dao.get_similar_pgvector(user_id, query_vec, top_k)
        results = [
            {
                "id": str(msg.id),
                "content": msg.content,
                "similarity": None,  # 필요시 SQL에서 select로 유사도 값도 받을 수 있음
                "timestamp": msg.timestamp.isoformat() if msg.timestamp else None
            }
            for msg in messages
        ]
        return results

    def update_message_vectors(self, user_id: uuid.UUID = None) -> Dict[str, Any]:
        """기존 메시지들의 벡터를 업데이트합니다."""
        try:
            # 특정 사용자 또는 전체 메시지 조회
            if user_id:
                messages = self.message_dao.get_all_by_user_id(user_id)
            else:
                messages = self.message_dao.get_all()

            total = len(messages)
            updated = 0
            errors = 0

            for msg in messages:
                if msg.vector is None:  # 벡터가 없는 메시지만 업데이트
                    try:
                        vector = get_embedding(msg.content)
                        self.message_dao.update(msg.id, vector=vector)
                        updated += 1
                    except Exception as e:
                        errors += 1

            result = {
                "total": total,
                "updated": updated,
                "errors": errors,
                "skipped": total - updated - errors
            }
            return result

        except Exception as e:
            raise
