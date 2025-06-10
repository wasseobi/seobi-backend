"""General Agent state management."""
from typing import Annotated, List, Dict
from typing_extensions import TypedDict
from langgraph.graph.message import add_messages

class State(TypedDict):
    """General Agent의 상태를 나타내는 타입"""
    messages: Annotated[list, add_messages] 