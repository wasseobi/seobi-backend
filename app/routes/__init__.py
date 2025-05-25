from app import api
from .auth import ns as auth_ns
from .session import ns as session_ns
from .message import ns as message_ns

# Register production namespaces
api.add_namespace(auth_ns)
api.add_namespace(session_ns)
api.add_namespace(message_ns)