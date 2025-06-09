def get_current_step_message(tool: str, status: str) -> str:
    tool_kor = {
        "google_search_expansion": "google search",
        "search_web": "web search",
        # 필요시 추가
    }
    status_kor = {
        "pending": "대기 중",
        "running": "작업 중",
        "done": "완료",
        "failed": "실패"
    }
    tool_msg = tool_kor.get(tool, tool)
    status_msg = status_kor.get(status, status)
    return f"{tool_msg} {status_msg}"