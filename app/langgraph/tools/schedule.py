from langchain_core.tools import tool
from flask import request, g
from app.services.schedule_service import ScheduleService
from app.utils.text_cleaner import clean_simple_text


@tool
def create_schedule_llm(text: str) -> dict:
    """
    새로운 일정을 추가하는 도구입니다.
    - "일정 추가", "회의 잡아줘", "스케줄 등록" 등 일정/스케줄 관련 명령에만 사용하세요.
    - 과거 대화/기억 검색에는 사용하지 마세요.
    Args:
        text (str): 일정 내용(자연어)
    Returns:
        dict: 생성된 일정 정보 및 안내 메시지
    """
    schedule_service = ScheduleService()
    user_id = None
    if hasattr(g, 'user_id') and g.user_id:
        user_id = g.user_id
    elif request.headers.get('user_id'):
        user_id = request.headers.get('user_id')
    elif request.json and request.json.get('user_id'):
        user_id = request.json.get('user_id')
    if not user_id:
        raise ValueError("user_id를 찾을 수 없습니다. 인증 또는 세션 정보를 확인하세요.")
    import uuid
    try:
        uuid.UUID(user_id)
    except Exception:
        raise ValueError("user_id는 반드시 UUID 형식이어야 합니다.")
    schedule = schedule_service.create_llm(user_id, text)
    # 안내 메시지를 최상단에 배치
    message = f"'{clean_simple_text(schedule.title)}' 일정이 등록되었습니다! 필요시 준비물: {clean_simple_text(schedule.memo) if schedule.memo else '없음'}"
    result = {
        'message': message,
        'id': str(schedule.id),
        'user_id': str(schedule.user_id),
        'title': clean_simple_text(schedule.title),
        'repeat': schedule.repeat,
        'start_at': schedule.start_at.isoformat() if schedule.start_at else None,
        'finish_at': schedule.finish_at.isoformat() if schedule.finish_at else None,
        'location': clean_simple_text(schedule.location),
        'status': schedule.status,
        'memo': clean_simple_text(schedule.memo),
        'linked_service': schedule.linked_service,
        'created_at': schedule.created_at.isoformat() if hasattr(schedule, 'created_at') and schedule.created_at else None,
    }
    return result


@tool
def get_user_schedules() -> list:
    """
    사용자의 모든 일정을 조회하는 도구입니다.
    - "내 일정 보여줘", "이번주 스케줄 알려줘" 등 일정 조회 명령에만 사용하세요.
    - 과거 대화/기억 검색에는 사용하지 마세요.
    Returns:
        list: 일정 정보 리스트
    """
    schedule_service = ScheduleService()
    user_id = None
    if hasattr(g, 'user_id') and g.user_id:
        user_id = g.user_id
    elif request.headers.get('user_id'):
        user_id = request.headers.get('user_id')
    elif request.json and request.json.get('user_id'):
        user_id = request.json.get('user_id')
    if not user_id:
        raise ValueError("user_id를 찾을 수 없습니다. 인증 또는 세션 정보를 확인하세요.")
    import uuid
    try:
        uuid.UUID(user_id)
    except Exception:
        raise ValueError("user_id는 반드시 UUID 형식이어야 합니다.")
    schedules = schedule_service.get_user_schedules(user_id)
    return [
        {
            'id': str(s.id),
            'user_id': str(s.user_id),
            'title': clean_simple_text(s.title),
            'repeat': s.repeat,
            'start_at': s.start_at.isoformat() if s.start_at else None,
            'finish_at': s.finish_at.isoformat() if s.finish_at else None,
            'location': clean_simple_text(s.location),
            'status': s.status,
            'memo': clean_simple_text(s.memo),
            'linked_service': s.linked_service,
            'created_at': s.created_at.isoformat() if hasattr(s, 'created_at') and s.created_at else None,
        }
        for s in schedules
    ]
