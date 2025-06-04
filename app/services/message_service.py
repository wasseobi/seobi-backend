from app.dao.message_dao import MessageDAO
from app.models import Session
from app.utils.message.message_context import MessageContext

from app.utils.openai_client import get_openai_client, get_embedding
from app.utils.message.processor import MessageProcessor
from app.langgraph.agent.executor import create_agent_executor
from app.langgraph.agent.graph import build_graph

from langchain.schema import HumanMessage, AIMessage
from langchain_core.messages import BaseMessage, ToolMessage
from typing import List, Dict, Any, Generator, Union, Optional
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
        if session.finish_at:
            raise ValueError('Cannot get messages from finished session')

        messages = self.message_dao.get_all_by_session_id(session_id)
        serialized = [self._serialize_message(msg) for msg in messages]
        return serialized

    def get_conversation_history(self, session_id: uuid.UUID) -> List[Dict[str, str]]:
        """Get conversation history formatted for AI completion"""
        session = Session.query.get(session_id)
        if not session:
            raise ValueError('Session not found')
        if session.finish_at:
            raise ValueError('Cannot get messages from finished session')

        messages = self.message_dao.get_all_by_session_id(session_id)
        return [
            {"role": msg.role, "content": msg.content}
            for msg in messages
        ]

    def create_message(self, session_id: uuid.UUID, user_id: uuid.UUID,
                       content: str, role: str, metadata) -> Dict:
        """Create a new message (임베딩 벡터 포함)"""
        session = Session.query.get(session_id)
        if not session:
            raise ValueError('Session not found')
        if session.finish_at:
            raise ValueError('Cannot add message to finished session')

        try:
            client = get_openai_client()
            vector = get_embedding(client, content)
        except Exception as e:
            vector = None

        message = self.message_dao.create(
            session_id, user_id, content, role, vector, metadata)
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
                                    content: str = None, messages: List[Union[BaseMessage, Dict[str, Any]]] = None) -> Generator[Dict, None, None]:
        """LangGraph를 통한 응답 생성. (자연어 쿼리 → 벡터검색 → 요약/답변)"""
        # 1. 벡터 검색 (user_id, content 기준 top3)
        similar_msgs = self.search_similar_messages_pgvector(user_id, content, 3)
        if not similar_msgs:
            # 2. fallback 답변
            yield {
                'type': 'chunk',
                'content': '그런 내용이 있었나요오? 기억이 안나요오 ㅜ',
                'metadata': {'fallback': True}
            }
            yield {
                'type': 'end',
                'context_saved': False
            }
            return
        # 3. 메시지 요약 프롬프트 생성
        summary_prompt = """아래는 사용자의 과거 대화 내용입니다. 이 중에서 현재 질문과 관련된 핵심 내용을 요약해서 자연어로 설명해 주세요.\n\n"""
        for i, msg in enumerate(similar_msgs, 1):
            summary_prompt += f"[{i}] {msg['content']}\n"
        summary_prompt += f"\n위 내용을 바탕으로, 사용자가 '{content}'라고 물었을 때 자연스럽게 답변해 주세요."
        # 4. LLM 호출 (LangGraph 기존 플로우 활용)
        processor = MessageProcessor(str(session_id), str(user_id))
        context = self._get_or_create_context(str(session_id), str(user_id))
        context.add_user_message(content)
        yield {
            'type': 'start',
            'user_message': {'content': content}
        }
        # summary_prompt를 첫 메시지로 사용
        messages = [HumanMessage(content=summary_prompt)]
        initial_state = {"messages": messages}
        for msg_chunk, metadata in self.graph.stream(initial_state, stream_mode="messages"):
            try:
                chunk_data = None
                if isinstance(msg_chunk, AIMessage):
                    if msg_chunk.content:
                        context.append_assistant_content(msg_chunk.content)
                        chunk_data = {
                            'type': 'chunk',
                            'content': msg_chunk.content,
                            'metadata': metadata
                        }
                        if chunk_data and chunk_data.get('content'):
                            yield chunk_data
            except Exception:
                continue
        context.finalize_assistant_response()
        self._save_context_messages(context)
        yield {
            'type': 'end',
            'context_saved': True
        }

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
            for message in messages:
                try:
                    # timestamp는 메타데이터에서 DB 필드로 이동
                    if "timestamp" in message:
                        timestamp = message.pop("timestamp")
                    else:
                        timestamp = datetime.now(timezone.utc).isoformat()
                    metadata = message.get("metadata", {})
                    if isinstance(metadata, dict) and "timestamp" in metadata:
                        del metadata["timestamp"]
                    self.create_message(
                        session_id=session_id,
                        user_id=user_id,
                        content=message["content"],
                        role=message["role"],
                        metadata=metadata
                    )
                except Exception:
                    raise
            self.active_contexts.pop(context.session_id, None)
        except Exception as e:
            raise

    def search_similar_messages(self, user_id: str, query: str, top_k: int = 5) -> list[dict]:
        """
        user_id로 해당 사용자의 모든 메시지 벡터를 불러와 쿼리 임베딩과의 유사도를 계산, top-N 결과 반환
        """
        import json
        user_uuid = uuid.UUID(user_id) if not isinstance(
            user_id, uuid.UUID) else user_id
        messages = self.message_dao.get_all_by_user_id(user_uuid)
        if not messages:
            return []

        # 쿼리 임베딩 생성
        client = get_openai_client()
        query_vec = np.array(get_embedding(client, query))

        # 각 메시지와의 코사인 유사도 계산
        results = []
        for msg in messages:
            if msg.vector is not None:
                msg_vec = np.array(msg.vector)
                sim = float(np.dot(query_vec, msg_vec) /
                            (np.linalg.norm(query_vec) * np.linalg.norm(msg_vec)))
                results.append({
                    "id": str(msg.id),
                    "content": msg.content,
                    "similarity": sim,
                    "timestamp": msg.timestamp.isoformat() if msg.timestamp else None
                })
        # 유사도 내림차순 정렬 후 top_k 반환
        results.sort(key=lambda x: x["similarity"], reverse=True)
        return results[:top_k]

    def search_similar_messages_pgvector(self, user_id: str, query: str, top_k: int = 5) -> list[dict]:
        """
        [PGVECTOR] user_id의 메시지 중 쿼리 임베딩과 가장 유사한 top_k 메시지 반환 (DB에서 벡터 연산)
        """
        client = get_openai_client()
        query_vec = np.array(get_embedding(client, query))

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

            client = get_openai_client()
            for msg in messages:
                if msg.vector is None:  # 벡터가 없는 메시지만 업데이트
                    try:
                        vector = get_embedding(client, msg.content)
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
