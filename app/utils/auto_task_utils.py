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

# Swagger None UI Error 대처
def safe_background_response(data: dict) -> dict:
    result = {
        'user_id': data.get('user_id') or "",
        'finished': bool(data.get('finished'))
    }
    if data.get('task') is not None:
        result['task'] = data['task']
    if data.get('all_task_done'):
        result['all_task_done'] = data['all_task_done']
    if data.get('error'):
        result['error'] = data['error']
    if data.get('step') is not None:
        result['step'] = data['step']
    return result