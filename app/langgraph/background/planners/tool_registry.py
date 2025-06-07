from typing import List, Callable, Optional
from app.langgraph.tools import agent_tools

ALLOWED_TOOL_NAMES = {"search_web", "google_search_expansion"}

def get_available_tools() -> List[str]:
    """
    전체 agent_tools 중 사용자가 사용할 수 있는 도구만 필터링해 반환한다.

    현재는 user_id와 관계없이 whitelist에 명시된 도구만 반환함.
    추후 사용자 등급/권한 기반 필터링 가능.
    get_available_tools_for_user(user_id)
    """
    return [
        tool.name
        for tool in agent_tools
        if hasattr(tool, "name") and tool.name in ALLOWED_TOOL_NAMES
    ]

def get_tool_by_name(name: str) -> Optional[Callable]:
    """허용된 도구 중에서 이름이 일치하는 도구 반환 (없으면 None)"""
    if name not in get_available_tools():
        return None

    for tool in agent_tools:
        if getattr(tool, "name", None) == name:
            return tool
    return None
