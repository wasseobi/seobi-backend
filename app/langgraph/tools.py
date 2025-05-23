"""사용 가능한 도구들을 정의하는 모듈입니다

사용 가능한 도구 목록:
1. get_current_time:
   - 설명: 현재 시간을 반환합니다
   - 인자: 없음
   - 응답 형식: "현재 시각은 HH시 MM분 SS초 입니다"

2. google_search:
   - 설명: 구글 검색을 수행합니다
   - 필수 인자:
     - query (str): 검색할 키워드나 문장
   - 선택 인자:
     - num_results (int): 가져올 결과 수 (기본값: 3)
   - 응답 형식: [{"title": "제목", "link": "URL", "snippet": "내용"}]

3. schedule_meeting:
   - 설명: 회의 일정을 등록합니다
   - 필수 인자:
     - datetime_str (str): 회의 시작 시간 (ISO 형식: "YYYY-MM-DDTHH:MM:SS")
   - 선택 인자:
     - duration (str): 회의 지속 시간 (기본값: "1h")
     - title (str): 회의 제목 (기본값: "회의")
     - attendees (List[str]): 참석자 이메일 목록
   - 응답 형식: {"success": true, "meeting_id": "ID", "details": {...}}

"""

import datetime
import os
from typing import List, Dict, Any

from langchain_core.tools import Tool, tool
from langchain_google_community import GoogleSearchAPIWrapper


@tool("get_current_time")
def get_current_time() -> str:
    """현재 시간을 반환합니다.

    Returns:
        str: 현재 시간을 포함한 응답 메시지
    """
    current_time = datetime.datetime.now()
    formatted_time = current_time.strftime("%H시 %M분 %S초")
    return f"현재 시각은 {formatted_time} 입니다."


@tool("google_search")
def google_search(query: str, num_results: int = 3) -> List[Dict[str, str]]:
    """Google 검색을 수행합니다.

    Args:
        query (str): 검색할 키워드나 문장
        num_results (int, optional): 가져올 결과 수. 기본값 3.

    Returns:
        List[Dict[str, str]]: 검색 결과 리스트. 각 결과는 title, link, snippet을 포함
    """
    try:
        api_key = os.getenv('GOOGLE_API_KEY')
        cse_id = os.getenv('GOOGLE_CSE_ID')
        if not api_key or not cse_id:
            return [{"error": "환경 변수 GOOGLE_API_KEY 또는 GOOGLE_CSE_ID가 비어 있습니다."}]
        if not isinstance(query, str):
            return [{"error": f"검색어(query)는 문자열이어야 합니다. 현재 타입: {type(query)}"}]
        if not isinstance(num_results, int):
            return [{"error": f"num_results는 int여야 합니다. 현재 타입: {type(num_results)}"}]
        search = GoogleSearchAPIWrapper(
            google_api_key=api_key,
            google_cse_id=cse_id
        )
        results = search.results(query, num_results=num_results)
        return results

    except Exception as e:
        return [{"error": f"검색 중 오류 발생: {str(e)}"}]


@tool("schedule_meeting")
def schedule_meeting(
    datetime_str: str,
    duration: str = "1h",
    title: str = "회의",
    attendees: List[str] = None
) -> Dict[str, Any]:
    """회의 일정을 등록합니다.

    Args:
        datetime_str (str): 회의 시작 시간 (ISO 형식)
        duration (str, optional): 회의 지속 시간. 기본값 "1h"
        title (str, optional): 회의 제목. 기본값 "회의"
        attendees (List[str], optional): 참석자 목록

    Returns:
        Dict[str, Any]: 등록된 회의 정보
    """
    try:
        # 실제로는 여기서 MCP나 캘린더 API를 호출
        meeting_id = "meeting_" + datetime.datetime.now().strftime("%Y%m%d%H%M%S")

        return {
            "success": True,
            "meeting_id": meeting_id,
            "details": {
                "title": title,
                "datetime": datetime_str,
                "duration": duration,
                "attendees": attendees or []
            }
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }


# 도구 객체 리스트 (Tool.from_function 제거, 데코레이터 기반 자동 수집)
tools = [
    get_current_time,
    google_search,
    schedule_meeting
]


def get_tools():
    """ToolNode 등에서 사용할 수 있도록 tools 리스트를 반환하는 함수"""
    return tools


"""
새로운 도구 추가 예시:
1. 도구 함수 정의:
```python
@tool("send_email")  # 도구 이름 지정
def send_email(
    to: List[str],           # 필수 인자
    subject: str = "제목",    # 선택 인자 (기본값 지정)
    body: str = ""           # 선택 인자
) -> Dict[str, Any]:         # 반환 타입 지정
    \"""이메일을 전송합니다.
    
    Args:
        to (List[str]): 수신자 이메일 목록
        subject (str, optional): 이메일 제목
        body (str, optional): 이메일 내용
        
    Returns:
        Dict[str, Any]: 전송 결과
            - success (bool): 성공 여부
            - message_id (str): 전송된 메시지 ID
    \"""
    # 구현...
    return {
        "success": True,
        "message_id": "generated_id"
    }
```

2. parse_intent.py의 시스템 프롬프트에 도구 정보 추가:
```
4. 이메일 전송
   - Tool: send_email
   - 필수: 이메일 관련 요청에 사용
   - 형식: {"tool_calls":[{
       "type":"function",
       "function":{
           "name":"send_email",
           "arguments":{
               "to":["user@example.com"],
               "subject":"제목",
               "body":"내용"
           }
       }
   }]}
```
"""
