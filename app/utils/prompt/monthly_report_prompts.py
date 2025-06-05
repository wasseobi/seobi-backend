MONTHLY_ACHIEVEMENTS_PROMPT = """
[월간 일정 성과 요약]
기간: {year}년 {month}월

분석 데이터:
- 전체 일정 수: {total_schedules}
- 완료된 일정: {completed_schedules}
- 달성률: {completion_rate}%

주요 패턴:
요일별 분포:
{day_distribution}

시간대별 분포:
{hour_distribution}

이 데이터를 바탕으로 {month}월 일정 관리에 대한 성과를 분석해주세요.
다음 내용을 포함해야 합니다:
1. 전반적인 일정 관리 성과
2. 발견된 패턴과 그 의미
3. 개선점이나 칭찬할 점
4. 다음 달을 위한 제안
"""

WEEKLY_TRENDS_PROMPT = """
[주차별 대화 흐름 분석]
기간: {year}년 {month}월

각 주차별 주요 내용:
{weekly_summaries}

위 내용을 바탕으로 {month}월의 주차별 대화 흐름을 분석해주세요.
다음 내용을 포함해야 합니다:
1. 각 주의 핵심 주제나 이슈
2. 주차별 변화나 발전 사항
3. 전체적인 월간 대화 흐름의 특징
4. 주목할 만한 패턴이나 인사이트
"""

INTEREST_TRENDS_PROMPT = """
[관심사 및 인사이트 트렌드 분석]
기간: {year}년 {month}월

관심사:
{interests}

인사이트:
{insights}

위 데이터를 바탕으로 {month}월 관심사와 인사이트 트렌드를 분석해주세요.
다음 내용을 포함해야 합니다:
1. 주요 관심 분야와 그 변화
2. 새롭게 발견된 관심사
3. 의미 있는 인사이트와 그 의미
4. 관심사간 연관성이나 패턴
"""

NEXT_MONTH_GOALS_PROMPT = """
[다음 달 목표 및 일정 제안]
현재: {year}년 {month}월

분석 데이터:
- 이번 달 성과: {achievements}
- 주요 관심사: {interests}
- 현재 진행중인 일정: {ongoing_schedules}

위 정보를 바탕으로 다음 달 목표와 일정을 제안해주세요.
다음 내용을 포함해야 합니다:
1. 주요 목표 3가지
2. 구체적인 실천 방안
3. 시간 관리 제안
4. 특별히 주의해야 할 점
"""

MONTHLY_REPORT_PROMPT = """
[{year}년 {month}월 월간 리포트]

{monthly_achievements}

{weekly_trends}

{interest_trends}

{next_month_goals}

이상의 내용을 바탕으로 {month}월을 종합적으로 정리하고,
다음 달을 위한 제안을 해주세요.
"""

MONTHLY_SCRIPT_PROMPT = """
안녕하세요,
{year}년 {month}월 월간 리포트를 말씀드리겠습니다.

{monthly_achievements_script}

{weekly_trends_script}

{interest_trends_script}

{next_month_goals_script}

이상으로 {month}월 월간 리포트를 마치겠습니다.
다음 달에도 함께하겠습니다.
감사합니다.
"""
