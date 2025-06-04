import uuid
import numpy as np
from typing import List, Optional

from app.models import Message
from app.dao.base import BaseDAO

class MessageDAO(BaseDAO[Message]):
    """Data Access Object for Message model"""
    
    def __init__(self):
        super().__init__(Message)

    def get_by_id(self, message_id: uuid.UUID) -> Optional[Message]:
        return self.get(str(message_id))

    def get_all(self) -> List[Message]:
        """Get all messages ordered by timestamp"""
        return self.query().order_by(Message.timestamp.asc()).all()

    def get_all_by_user_id(self, user_id: uuid.UUID) -> List[Message]:
        """Get all messages for a user ordered by timestamp"""
        return self.query().filter_by(user_id=user_id).order_by(Message.timestamp.desc()).all()

    def get_all_by_session_id(self, session_id: uuid.UUID) -> List[Message]:
        """Get all messages in a session ordered by timestamp"""
        return self.query().filter_by(session_id=session_id).order_by(Message.timestamp.asc()).all()

    def create(self, session_id: uuid.UUID, user_id: uuid.UUID, 
                      content: str, role: str, vector=None, metadata=None,
                      keyword_text=None, keyword_vector=None) -> Message:
        """Create a new message (vector 임베딩, 키워드 포함)"""
        return super().create(
            session_id=session_id,
            user_id=user_id,
            content=content,
            role=role,
            vector=vector,
            message_metadata=metadata,
            keyword_text=keyword_text,
            keyword_vector=keyword_vector
        )

    def update(self, message_id: uuid.UUID, **kwargs) -> Optional[Message]:
        return super().update(str(message_id), **kwargs)

    def get_similar_pgvector(self, user_id, query_vector, top_k=5):
        """
        [PGVECTOR] user_id의 메시지 중 query_vector와 가장 유사한 top_k 메시지 반환
        (pgvector 연산자 사용, DB에서 직접 유사도 계산)
        """
        if isinstance(query_vector, np.ndarray):
            query_vector = query_vector.tolist()
        return (
            self.query()
            .filter(Message.user_id == user_id)
            .filter(Message.vector != None)
            .order_by(Message.vector.l2_distance(query_vector))  # 또는 .cosine_distance(query_vector)
            .limit(top_k)
            .all()
        )

    def get_keyword_pgvector(self, user_id, query_vector, top_k=5):
        """
        [PGVECTOR] user_id의 메시지 중 query_vector와 가장 유사한 top_k keyword 반환 (keyword_vector 기준)
        """
        if isinstance(query_vector, np.ndarray):
            query_vector = query_vector.tolist()
        return (
            self.query()
            .filter(Message.user_id == user_id)
            .filter(Message.keyword_vector != None)
            .order_by(Message.keyword_vector.l2_distance(query_vector))  # 또는 .cosine_distance(query_vector)
            .limit(top_k)
            .all()
        )
