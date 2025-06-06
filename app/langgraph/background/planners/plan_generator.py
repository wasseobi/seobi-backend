from typing import List, Dict, Any
from app.utils.openai_client import get_openai_client, get_completion
import json

# ✏️ 프롬프트 템플릿 정의
# TODO: 프롬프트 파일에 분리하기
PLAN_GENERATION_PROMPT = """
당신은 작업 자동화를 위한 AI 계획자입니다.
아래의 업무 제목과 업무 설명을 바탕으로, 해당 업무 실행 계획은 사용 가능한 도구 목록을 참고하여 JSON 리스트 형태로 작성해 주세요.

업무 제목: {title}
업무 설명: {description}

사용 가능한 도구 목록: {tool_names}

요구 사항:
- 전체 계획은 JSON 리스트 형태로 출력되어야 합니다. 각 항목은 다음 필드를 포함해야 합니다:
  - step_id: 고유 식별자 (예: "search_google")
  - tool: 사용할 도구 이름 (tool_names 중에서 선택)
  - objective: 이 단계에서 달성하고자 하는 세부 목표 (예: "요약 정리", "자료 수집")
  - depends_on: 선행 작업의 step_id 리스트 (없으면 빈 리스트)


규칙:
- step_id는 모든 단계에서 중복 없이 고유해야 합니다. 필요 시 숫자를 붙여 고유하게 만드세요.
  - 예: "gather_news_1", "summarize_result", "gather_news_2", "send_email"
- **요약, 정리, 문서화, 작성, 결과 출력, 확인 등의 단계는 이 계획에 포함하지 마세요.**
- 사용 가능한 도구 목록에 있는 도구를 적절히 분배하여 단계별 실행 흐름을 구성하세요.
- 사용 가능한 도구 목록에 해당 목적에 맞는 도구가 없으면, 해당 단계는 실행 계획에 포함하지 마세요.
- 반드시 사용 가능한 도구 목록에 있는 도구 중에서 선택하고, 해당 단계의 objective(목표)와 기능적으로 일치해야 합니다.
    - 예: 
        - "뉴스 수집" → google_news
        - "정보 검색" → search_web, google_search
- 사용 가능한 도구는 여러 단계에서 반복해서 사용할 수 있습니다.
- step 간 의존 관계를 명확히 정의하고, 실행 순서를 고려해 적절히 depends_on을 설정하세요.
- JSON 리스트만 출력하세요. 추가 설명, 주석, 마크다운 등은 포함하지 마세요.

예시 입력:
업무 제목: 클라우드 컴퓨팅 기본 개념 조사 및 문서화
업무 설명: 클라우드 컴퓨팅의 정의, 특징, 활용 사례 등을 조사하고 정리하여 팀원이 쉽게 이해할 수 있도록 문서화합니다.
사용 가능한 도구 목록: "search_web", "google_search", "google_news"

예시 출력:
[
  {{
    "step_id": "gather_recent_news",
    "tool": "google_news",
    "objective": "클라우드 컴퓨팅에 대한 최신 정보 수집",
    "depends_on": []
  }},
  {{
    "step_id": "search_google",
    "tool": "google_search",
    "objective": "수집된 정보를 포함해 클라우드 컴퓨팅의 개념, 특징, 활용사례 검색",
    "depends_on": ["gather_recent_news"]
  }}
]
"""

def generate_plan_steps(title: str, description: str, tool_names: List[str]) -> List[Dict[str, Any]]:
    """
    LLM을 이용해 PlanStep 리스트를 생성합니다.

    Args:
        title (str): 업무 제목
        description (str): 업무 설명
        tool_names (List[str]): 사용할 수 있는 도구 이름 리스트

    Returns:
        List[Dict[str, Any]]: PlanStep 리스트 (LLM 응답 파싱 결과)
    """
    prompt = PLAN_GENERATION_PROMPT.format(
        title=title,
        description=description,
        tool_names=", ".join(tool_names)
    )

    client = get_openai_client()
    messages = [
        {"role": "system", "content": "너는 체계적인 AI 업무 계획자야. JSON 형식으로 정확히 출력해."},
        {"role": "user", "content": prompt}
    ]

    try:
        response = get_completion(client, messages)
        plan = json.loads(response.strip())
        if isinstance(plan, list):
            return plan
        raise ValueError("LLM 응답이 리스트 형식이 아님")
    except Exception as e:
        raise RuntimeError(f"Plan 생성 중 오류 발생: {str(e)}")
