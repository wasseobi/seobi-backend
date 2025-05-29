"""Cleanup graph prompts."""

ANALYSIS_PROMPT = """다음 대화를 분석하여 주요 인사이트를 추출해주세요:

1. 주요 논의 주제
2. 언급된 액션 아이템이나 작업
3. 중요한 결정사항
4. 후속 조치가 필요한 항목

응답은 다음 키를 가진 JSON 객체 형식으로 작성해주세요:
- topics: 주요 주제 목록
- action_items: 작업/액션 아이템 목록
- decisions: 결정사항 목록
- follow_ups: 후속 조치 항목 목록

각 항목은 구체적이고 명확하게 작성해주세요."""

TASK_GENERATION_PROMPT = """다음 대화 분석 결과를 바탕으로 AI가 수행해야 할 구체적인 업무들을 생성해주세요:

분석 결과:
{analysis_result}

각 업무에 대해 다음 정보를 포함해주세요:
1. 업무 설명
2. 우선순위 (high/medium/low)
3. 예상 소요 시간 (시간 단위)
4. 의존성 (있는 경우)

응답은 다음 키를 가진 JSON 배열 형식으로 작성해주세요:
- description: 업무 설명
- priority: 우선순위
- effort: 예상 소요 시간
- dependencies: 의존 업무 목록

각 업무는 구체적이고 실행 가능한 형태로 작성해주세요.""" 