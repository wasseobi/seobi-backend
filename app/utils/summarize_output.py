from typing import Any, Optional
from app.utils.openai_client import _get_openai_client, get_completion
from app.utils.text_cleaner import clean_text
import json
import re

# TODO: 프롬프트 파일로 분리
SUMMARY_PROMPT_WITH_CONTEXT = """
너는 목적에 맞게 핵심 내용 중심으로 요약하고,
주어진 목적(objective)에 얼마나 잘 부합하는지를 평가하는 요약 및 평가 전문가야.

다음 항목을 참고하여 요약을 수행해야 해:
- 도구 이름: {tool_name}
- 목적: {objective}
- 수집된 정보: {raw_output}

수집된 정보는 {tool_name} 도구를 통해 얻은 콘텐츠야. 
수집된 정보에서 목적(Objective)에 맞춰 핵심 내용을 중심으로 정리하는 것이 가장 중요해.

요약 결과는 반드시 아래 출력 예시처럼 **`output`과 `quality_score`라는 고정된 키 이름을 갖는 JSON 형식**으로 작성해줘.
- `output`: bullet point 요약 (300자 이내)
- `quality_score`: 목적에 얼마나 부합하는지 0.0 ~ 1.0 점수로 평가 (float)

입력 예시:
{{
  "tool_name": "google_news",
  "objective": "클라우드 컴퓨팅에 대한 최신 정보 수집",
  "raw_output": {{
    "articles": [
      {{"title": "AI 통합 확대", "snippet": "AI와 클라우드의 결합이 급속히 진행 중"}},
      {{"title": "클라우드 보안 이슈", "snippet": "보안 문제로 인한 시장 불안 커져"}}
    ]
  }}
}}

출력 예시:
{{
  "output": [
    "- 클라우드 기술과 AI의 통합이 빠르게 진행 중",
    "- 보안 우려가 주요 이슈로 부상"
  ],
  "quality_score": 0.8
}}

"""
def gpt_summarize_output(
    output: Any,
    tool_name: Optional[str] = None,
    objective: Optional[str] = None,
) -> dict:
    """
    LLM을 이용해 도구 output을 요약하고, objective 부합도를 평가합니다.
    - 결과는 Dict[str, Any] 형식으로 출력되며 quality_score가 포함됩니다.
    """
    client = _get_openai_client()

    try:
        if isinstance(output, list):
            output = [
                {
                    "title": item.get("title"),
                    "snippet": clean_text(
                        item.get("snippet") if isinstance(item.get("snippet"), str)
                        else item.get("content") if isinstance(item.get("content"), str)
                        else str(item.get("snippet") or item.get("content") or "")
                    )[:300]
                }
                for item in output
            ]

        raw_output = json.dumps(output, indent=2, ensure_ascii=False)
        if len(raw_output) > 6000:
            raw_output = raw_output[:6000]

        prompt = SUMMARY_PROMPT_WITH_CONTEXT.format(
            tool_name=tool_name or "",
            objective=objective or "",
            raw_output=raw_output
        )

        messages = [
            {"role": "system", "content": "너는 목적에 맞게 요약하고 평가하는 전문가야."},
            {"role": "user", "content": prompt}
        ]

        response = get_completion(client, messages)

        match = re.search(r'```json\s*({[\s\S]*?})\s*```', response)
        if match:
            response_json = match.group(1)
            return json.loads(response_json)

        match = re.search(r'({[\s\S]*})', response)
        if match:
            response_json = match.group(1)
            return json.loads(response_json)

        return json.loads(response.strip())

    except json.JSONDecodeError:
        print("[gpt_summarize_output] JSON 파싱 실패")
        print(f"[gpt_summarize_output] LLM 응답(파싱실패): {response}")
        return {"output": ["(요약 결과 파싱 실패)"], "quality_score": 0.0}
    except Exception as e:
        print(f"[gpt_summarize_output] 요약 실패: {type(e).__name__} - {str(e)}")
        return {"output": ["(LLM 요약 실패)"], "quality_score": 0.0}
