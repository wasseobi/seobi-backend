from app.dao.message_dao import MessageDAO
from app.services.session_service import SessionService
from app.models import Session
from app.utils.openai_client import get_openai_client, get_completion
from app.langgraph.graph import builder as langgraph_builder
from langchain.schema import HumanMessage
from typing import List, Dict, Any
import uuid

class MessageService:
    def __init__(self):
        self.dao = MessageDAO()
        self.session_service = SessionService()

    def _serialize_message(self, message: Any) -> Dict[str, Any]:
        """Serialize message data for API response"""
        return {
            'id': str(message.id),
            'session_id': str(message.session_id),
            'user_id': str(message.user_id),
            'content': message.content,
            'role': message.role,
            'timestamp': message.timestamp.isoformat() if message.timestamp else None,
            'vector': message.vector.tolist() if message.vector is not None else None
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
                      content: str, role: str = 'user') -> Dict:
        """Create a new message"""
        session = Session.query.get(session_id)
        if not session:
            raise ValueError('Session not found')
        if session.finish_at:
            raise ValueError('Cannot add message to finished session')

        message = self.dao.create_message(session_id, user_id, content, role)
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

    def create_completion(self, session_id: uuid.UUID, user_id: uuid.UUID, 
                         content: str) -> Dict[str, Dict]:
        """Create a new message and get AI completion"""
        session = Session.query.get(session_id)
        if not session:
            raise ValueError('Session not found')
        if session.finish_at:
            raise ValueError('Cannot add message to finished session')

        # Create user message
        user_message = self.dao.create_message(session_id, user_id, content, 'user')

        # Get conversation history
        history = self.get_conversation_history(session_id)

        # Prepare messages for OpenAI
        messages = [
            {"role": "system", "content": "당신은 도움이 되는 AI 어시스턴트입니다. 응답은 간결하고 명확하게 해주세요."},
            *history,
            {"role": "user", "content": content}
        ]

        # Get AI completion
        try:
            client = get_openai_client()
            response = get_completion(client, messages)
        except Exception as e:
            raise ValueError(f"Failed to get AI completion: {str(e)}")

        # Create assistant message
        assistant_message = self.dao.create_message(session_id, user_id, response, 'assistant')

        # Update session title and description if this is the first message
        if len(history) == 1:
            self.session_service.update_title_description_from_conversation(
                session_id, content, response
            )

        return {
            'user_message': self._serialize_message(user_message),
            'assistant_message': self._serialize_message(assistant_message)
        }

    def create_langgraph_completion(self, session_id: uuid.UUID, user_id: uuid.UUID, content: str) -> Dict[str, Dict]:
        """LangGraph 기반으로 메시지 생성 및 AI 응답/저장"""
        session = Session.query.get(session_id)
        if not session:
            raise ValueError('Session not found')
        if session.finish_at:
            raise ValueError('Cannot add message to finished session')

        # 1. 사용자 메시지 저장
        user_message = self.dao.create_message(session_id, user_id, content, 'user')

        # 2. 랭그래프 상태 생성 및 실행
        initial_state = {
            "user_input": content,
            "parsed_intent": {},
            "reply": "",
            "action_required": False,
            "executed_result": {},
            "timestamp": user_message.timestamp.isoformat() if user_message.timestamp else None,
            "user_id": str(user_id),
            "tool_info": None,
            "messages": [HumanMessage(content=content)]
        }
        graph = langgraph_builder.compile()
        print("[DEBUG][service] graph type:", type(graph))
        print("[DEBUG][service] graph.invoke type:", type(getattr(graph, 'invoke', None)))
        print("[DEBUG][service] initial_state type:", type(initial_state))
        print("[DEBUG][service] initial_state:", initial_state)
        result = graph.invoke(initial_state)
        print("[DEBUG][service] graph.invoke 반환값 type:", type(result))
        print("[DEBUG][service] graph.invoke 반환값:", result)
        ai_reply = result.get("reply")
        # 3. AI 메시지 저장
        assistant_message = self.dao.create_message(session_id, user_id, ai_reply, 'assistant')
        return {
            'user_message': self._serialize_message(user_message),
            'assistant_message': self._serialize_message(assistant_message)
        }