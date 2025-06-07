from typing import Dict, Any, Optional
from app.utils.openai_client import get_completion
import json

# 툴별 입력 스키마 정의
# TODO: 프롬프트 파일에 분리하기 
TOOL_INPUT_SCHEMAS = {
    "search_web": {
        "query": "string (검색어)"
    },
    "google_search_expansion": {
        "query": "string (검색 키워드)",
        "num_results": "int (기본값 3)"
    },
    "google_news": {
        "query": "string (뉴스 키워드)",
        "num_results": "int (기본값 5)",
        "tbs": "string (기간 필터, 예: 'qdr:d2' → 최근 2일)"
    }
}

TOOL_INPUT_GENERATION_PROMPT = """
당신은 작업 자동화를 돕는 AI 어시스턴트입니다.

당신의 목적은: 
Objective에 명시된 목표를 달성할 수 있도록, 
주어진 도구(tool_name)를 정확히 실행하기 위한 입력값(JSON 형식)을 생성하는 것입니다.  
이를 위해 필요한 경우, 이전 단계의 출력 결과를 참고해 
현재 단계의 목적(Objective)에 적합한 결과를 얻을 수 있는 입력값을 구성해야 합니다.

도구 이름: {tool_name}
도구 입력 스키마: {schema_hint}
Objective: {objective}
이전 작업의 출력 결과 (참고용): {prior_outputs}

※ 이전 작업의 출력 결과는 존재할 경우에만 제공되며, 필요한 경우에 한해 참고하세요.

작성 규칙:
- 반드시 '도구 이름'에 맞는 '도구 입력 스키마'를 참고하여 필드를 모두 포함해 작성하세요.
- 출력은 반드시 JSON 오브젝트 형식으로 시작하고 끝나야 합니다.
- 설명, 주석, 마크다운 없이 **입력값 JSON만 출력**하세요.
- 모든 필드는 빠짐없이 포함하고, 입력값은 objective에 맞춰 적절하게 작성하세요.
- 형식 오류나 누락 없이 파싱 가능한 JSON이어야 합니다.

입력 예시:
tool_name: google_news
도구 입력 스키마:
{{
  "query": "string (뉴스 키워드)",
  "num_results": "int (기본값 5)",
  "tbs": "string (기간 필터, 예: 'qdr:d' → 최근 1일)"
}}
Objective: "클라우드 컴퓨팅에 대한 최신 정보 수집"

예시 출력:
{{"query": "클라우드 컴퓨팅 최신 동향", "num_results": 5, "tbs": "qdr:d"}}
"""

def format_tool_input(
    tool_name: str,
    objective: str,
    prior_outputs: Optional[Dict[str, Any]] = None
) -> Optional[Dict[str, Any]]:
    """
    PlanStep objective + prior_outputs → tool 실행용 입력값 JSON 생성

    Args:
        tool_name (str): 사용할 도구 이름
        objective (str): PlanStep 목적 설명
        prior_outputs (Dict[str, Any], optional): depends_on된 step들의 output 요약

    Returns:
        Optional[Dict[str, Any]]: 도구 실행에 필요한 입력값
    """

    # prior_outputs → 요약 문자열로 정리
    prior_outputs = json.dumps(prior_outputs or {}, indent=2, ensure_ascii=False)

    # 해당 tool의 입력 스키마
    schema_hint = json.dumps(
        TOOL_INPUT_SCHEMAS.get(tool_name, {}),
        indent=2,
        ensure_ascii=False
    )

    # LLM 프롬프트 구성
    prompt = TOOL_INPUT_GENERATION_PROMPT.format(
        tool_name=tool_name,
        schema_hint=schema_hint,
        objective=objective,
        prior_outputs=prior_outputs
    )

    messages = [
        {"role": "system", "content": "너는 objective와 이전 step 결과를 참고하여 도구 입력값 JSON을 정확히 생성하는 AI야."},
        {"role": "user", "content": prompt}
    ]

    try:
        print("[format_tool_input] called")  # 함수 진입 확인
        response = get_completion(messages)
        print(f"[format_tool_input] LLM 응답: {response}")  # 디버깅용
        parsed = json.loads(response.strip())
        print(f"[format_tool_input] 파싱 결과: {parsed}")  # 디버깅용
        return parsed
    except Exception as e:
        print(f"[format_tool_input] LLM 응답 파싱 실패: {type(e).__name__} - {str(e)}")
        print(f"[format_tool_input] response(예외 발생시): {locals().get('response', None)}")
        return None