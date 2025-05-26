from app.dao.message_dao import MessageDAO
from app.services.session_service import SessionService
from app.models import Session
from app.utils.message.message_context import MessageContext  # 새로 추가

from app.utils.openai_client import get_openai_client, get_embedding
from app.utils.message.processor import MessageProcessor
from app.utils.message.formatter import format_message_content
from app.langgraph.executor import create_agent_executor
from app.langgraph.graph import build_graph

from langchain.schema import HumanMessage, AIMessage
from langchain_core.messages import BaseMessage, ToolMessage
from typing import List, Dict, Any, Generator, Union, Optional
import uuid
from datetime import datetime, timezone
import logging
import json
import numpy as np

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)


class MessageService:
    def __init__(self):
        self.dao = MessageDAO()
        self.session_service = SessionService()
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
        messages = self.dao.get_all_messages()
        return [self._serialize_message(msg) for msg in messages]

    def get_message(self, message_id: uuid.UUID) -> Dict:
        """Get a message by ID"""
        message = self.dao.get_message_by_id(message_id)
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

        messages = self.dao.get_session_messages(session_id)
        return [self._serialize_message(msg) for msg in messages]

    def get_conversation_history(self, session_id: uuid.UUID) -> List[Dict[str, str]]:
        """Get conversation history formatted for AI completion"""
        session = Session.query.get(session_id)
        if not session:
            raise ValueError('Session not found')
        if session.finish_at:
            raise ValueError('Cannot get messages from finished session')

        messages = self.dao.get_session_messages(session_id)
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
            print(f"[임베딩] 벡터 생성 성공 - content: {content[:30]}...")
            logger.debug(f"[임베딩] 벡터 생성 성공 - content: {content[:30]}...")
        except Exception as e:
            print(f"[임베딩] 벡터 생성 실패: {str(e)}")
            logger.error(f"[임베딩] 벡터 생성 실패: {str(e)}")
            vector = None

        message = self.dao.create_message(
            session_id, user_id, content, role, vector, metadata)
        return self._serialize_message(message)

    def update_message(self, message_id: uuid.UUID, **kwargs) -> Dict:
        """Update a message"""
        message = self.dao.update_message(message_id, **kwargs)
        if not message:
            raise ValueError('Message not found')
        return self._serialize_message(message)

    def delete_message(self, message_id: uuid.UUID) -> bool:
        """Delete a message"""
        return self.dao.delete_message(message_id)

    def create_langgraph_completion(self, session_id: uuid.UUID, user_id: uuid.UUID,
                                    content: str = None, messages: List[Union[BaseMessage, Dict[str, Any]]] = None) -> Generator[Dict, None, None]:
        """LangGraph를 통한 응답 생성."""
        processor = MessageProcessor(str(session_id), str(user_id))
        context = self._get_or_create_context(str(session_id), str(user_id))
        final_response = []
        
        try:
            context.add_user_message(content if content is not None else messages[-1]['content'])
            print(f"[LangGraph] 사용자 입력: {content if content is not None else messages[-1]['content']}")
            logger.debug(f"[LangGraph] 사용자 입력: {content if content is not None else messages[-1]['content']}")
            yield {
                'type': 'start',
                'user_message': {'content': content}
            }
            messages = [HumanMessage(
                content=content if content is not None else messages[-1]['content'])]
            initial_state = {"messages": messages}
            for msg_chunk, metadata in self.graph.stream(initial_state, stream_mode="messages"):
                try:
                    chunk_data = None
                    print(f"[LangGraph] msg_chunk 타입: {type(msg_chunk)}, 내용: {str(msg_chunk)[:100]}")
                    logger.debug(f"[LangGraph] msg_chunk 타입: {type(msg_chunk)}, 내용: {str(msg_chunk)[:100]}")
                    if isinstance(msg_chunk, ToolMessage):
                        print(f"[LangGraph] ToolMessage 도착: {msg_chunk}")
                        logger.debug(f"[LangGraph] ToolMessage 도착: {msg_chunk}")
                        for processed in processor.process_ai_or_tool_message(msg_chunk):
                            context.add_tool_result(
                                tool_name=processed.get("metadata", {}).get("tool_name", "unknown"),
                                result=processed.get("content", "")
                            )
                            print(f"[LangGraph] ToolMessage 처리 결과: {processed}")
                            logger.debug(f"[LangGraph] ToolMessage 처리 결과: {processed}")
                            chunk_data = {
                                'type': 'chunk',
                                'content': processed.get("content", ""),
                                'metadata': {
                                    **processed.get("metadata", {}),
                                    "tool_response": True
                                }
                            }
                    elif isinstance(msg_chunk, AIMessage):
                        print(f"[LangGraph] AIMessage 도착: {msg_chunk}")
                        logger.debug(f"[LangGraph] AIMessage 도착: {msg_chunk}")
                        if hasattr(msg_chunk, "additional_kwargs") and msg_chunk.additional_kwargs.get("tool_calls"):
                            tool_calls = msg_chunk.additional_kwargs["tool_calls"]
                            print(f"[LangGraph] AIMessage tool_calls: {tool_calls}")
                            logger.debug(f"[LangGraph] AIMessage tool_calls: {tool_calls}")
                            context.add_tool_call_chunk(tool_calls[0])
                            chunk_data = {
                                'type': 'tool_calls',
                                'tool_calls': tool_calls
                            }
                        elif msg_chunk.content:
                            context.append_assistant_content(msg_chunk.content)
                            print(f"[LangGraph] AIMessage content: {msg_chunk.content}")
                            logger.debug(f"[LangGraph] AIMessage content: {msg_chunk.content}")
                            chunk_data = {
                                'type': 'chunk',
                                'content': msg_chunk.content,
                                'metadata': metadata
                            }
                    elif isinstance(msg_chunk, dict):
                        print(f"[LangGraph] dict msg_chunk: {msg_chunk}")
                        logger.debug(f"[LangGraph] dict msg_chunk: {msg_chunk}")
                        if "agent" in msg_chunk:
                            messages_to_process = msg_chunk["agent"].get("formatted_messages", [])
                            for processed in processor.process_agent_messages(messages_to_process):
                                if processed.get("content"):
                                    context.append_assistant_content(processed["content"])
                                    print(f"[LangGraph] agent 메시지 처리: {processed}")
                                    logger.debug(f"[LangGraph] agent 메시지 처리: {processed}")
                                    chunk_data = {
                                        'type': 'chunk',
                                        'content': processed["content"],
                                        'metadata': processed.get("metadata", {})
                                    }
                        elif "content" in msg_chunk or "metadata" in msg_chunk:
                            for processed in processor.process_dict_message(msg_chunk):
                                if processed.get("content"):
                                    context.append_assistant_content(processed["content"])
                                    print(f"[LangGraph] dict 메시지 처리: {processed}")
                                    logger.debug(f"[LangGraph] dict 메시지 처리: {processed}")
                                    chunk_data = {
                                        'type': 'chunk',
                                        'content': processed["content"],
                                        'metadata': processed.get("metadata", metadata)
                                    }
                    if chunk_data and chunk_data.get('content'):
                        final_response.append(chunk_data.get('content'))
                        print(f"[LangGraph] chunk_data 최종 content: {chunk_data.get('content')}")
                        logger.debug(f"[LangGraph] chunk_data 최종 content: {chunk_data.get('content')}")
                        yield chunk_data
                except Exception as processing_error:
                    print(f"[LangGraph] 메시지 처리 중 오류 발생: {str(processing_error)}")
                    logger.error(f"메시지 처리 중 오류 발생: {str(processing_error)}")
                    continue
            context.finalize_assistant_response()
            self._save_context_messages(context)
            if final_response:
                print(f"[AI응답] 최종:\n{json.dumps(''.join(final_response), ensure_ascii=False, indent=2)}")
                logger.debug(f"[AI응답] 최종:\n{json.dumps(''.join(final_response), ensure_ascii=False)}")
            yield {
                'type': 'end',
                'context_saved': True
            }
        except Exception as e:
            print(f"[LangGraph] LangGraph 완료 생성 중 오류 발생: {str(e)}")
            logger.error(f"LangGraph 완료 생성 중 오류 발생: {str(e)}")
            yield {
                'type': 'error',
                'error': str(e)
            }
            raise

    def get_user_messages(self, user_id: uuid.UUID) -> List[Dict]:
        """Get all messages for a user

        Args:
            user_id (uuid.UUID): User's ID

        Returns:
            List[Dict]: List of serialized messages for the user

        Raises:
            ValueError: If user_id is invalid
        """
        try:
            messages = self.dao.get_user_messages(user_id)
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

            logger.debug(f"메시지 저장 시작 - 세션: {session_id}")
            messages = context.get_messages_for_storage()
            logger.debug(f"저장할 메시지: {json.dumps(messages, ensure_ascii=False)}")

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

                    logger.debug(f"메시지 저장 시도: role={message['role']}, metadata={json.dumps(metadata, ensure_ascii=False)}")

                    self.create_message(
                        session_id=session_id,
                        user_id=user_id,
                        content=message["content"],
                        role=message["role"],
                        metadata=metadata
                    )
                    logger.debug(f"메시지 저장 성공: {message['role']}")
                except Exception as msg_error:
                    logger.error(f"개별 메시지 저장 실패: {str(msg_error)}")
                    raise

            # 컨텍스트 제거
            self.active_contexts.pop(context.session_id, None)
            logger.debug(f"모든 메시지 저장 완료 - 세션: {session_id}")

        except Exception as e:
            logger.error(f"메시지 저장 중 오류 발생: {str(e)}")
            raise

    def search_similar_messages_by_user_id(self, user_id: str, query: str, top_k: int = 5) -> list[dict]:
        """
        user_id로 해당 사용자의 모든 메시지 벡터를 불러와 쿼리 임베딩과의 유사도를 계산, top-N 결과 반환
        """
        import logging, json
        logger = logging.getLogger(__name__)
        print(f"[벡터검색] user_id: {user_id}, query: {query}, top_k: {top_k}")
        logger.debug(f"[벡터검색] user_id: {user_id}, query: {query}, top_k: {top_k}")
        user_uuid = uuid.UUID(user_id) if not isinstance(user_id, uuid.UUID) else user_id
        messages = self.dao.get_user_messages(user_uuid)
        print(f"[벡터검색] 불러온 메시지 수: {len(messages)}")
        logger.debug(f"[벡터검색] 불러온 메시지 수: {len(messages)}")
        if not messages:
            print("[벡터검색] 메시지가 없습니다.")
            logger.debug("[벡터검색] 메시지가 없습니다.")
            return []

        # 쿼리 임베딩 생성
        client = get_openai_client()
        query_vec = np.array(get_embedding(client, query))
        print(f"[벡터검색] 쿼리 임베딩: {json.dumps(query_vec.tolist(), ensure_ascii=False)}")
        logger.debug(f"[벡터검색] 쿼리 임베딩: {json.dumps(query_vec.tolist(), ensure_ascii=False)}")

        # 각 메시지와의 코사인 유사도 계산
        results = []
        for msg in messages:
            if msg.vector is not None:
                msg_vec = np.array(msg.vector)
                sim = float(np.dot(query_vec, msg_vec) / (np.linalg.norm(query_vec) * np.linalg.norm(msg_vec)))
                results.append({
                    "id": str(msg.id),
                    "content": msg.content,
                    "similarity": sim,
                    "timestamp": msg.timestamp.isoformat() if msg.timestamp else None
                })
        # 유사도 내림차순 정렬 후 top_k 반환
        results.sort(key=lambda x: x["similarity"], reverse=True)
        print(f"[벡터검색] 최종 반환 결과: {json.dumps(results[:top_k], ensure_ascii=False, indent=2)}")
        logger.debug(f"[벡터검색] 최종 반환 결과: {json.dumps(results[:top_k], ensure_ascii=False)}")
        return results[:top_k]

    def update_message_vectors(self, user_id: uuid.UUID = None) -> Dict[str, Any]:
        """기존 메시지들의 벡터를 업데이트합니다."""
        try:
            # 특정 사용자 또는 전체 메시지 조회
            if user_id:
                messages = self.dao.get_user_messages(user_id)
            else:
                messages = self.dao.get_all_messages()

            total = len(messages)
            updated = 0
            errors = 0
            
            print(f"[벡터 업데이트] 시작: 총 {total}개 메시지")
            logger.debug(f"[벡터 업데이트] 시작: 총 {total}개 메시지")

            client = get_openai_client()
            for msg in messages:
                if msg.vector is None:  # 벡터가 없는 메시지만 업데이트
                    try:
                        vector = get_embedding(client, msg.content)
                        self.dao.update_message(msg.id, vector=vector)
                        updated += 1
                        print(f"[벡터 업데이트] 성공 {updated}/{total}: {msg.content[:30]}...")
                        logger.debug(f"[벡터 업데이트] 성공 {updated}/{total}: {msg.content[:30]}...")
                    except Exception as e:
                        errors += 1
                        print(f"[벡터 업데이트] 실패 {msg.id}: {str(e)}")
                        logger.error(f"[벡터 업데이트] 실패 {msg.id}: {str(e)}")

            result = {
                "total": total,
                "updated": updated,
                "errors": errors,
                "skipped": total - updated - errors
            }
            print(f"[벡터 업데이트] 완료: {json.dumps(result, ensure_ascii=False)}")
            logger.debug(f"[벡터 업데이트] 완료: {json.dumps(result, ensure_ascii=False)}")
            return result

        except Exception as e:
            logger.error(f"벡터 업데이트 중 오류 발생: {str(e)}")
            raise
