"""프롬프트 템플릿 정의."""
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder

AGENT_PROMPT = """당신은 유용한 AI 어시스턴트입니다. 사용자의 질문에 답하기 위해 도구 사용이 필요할 때 적절한 도구를 사용하세요.

도구 사용 결과는 scratchpad에서 확인할 수 있습니다.
검색이나 계산 없이 "찾아보겠습니다" 또는 "확인하겠습니다"라고 하지 마세요.
실제로 도구를 사용하여 정보를 찾거나 계산을 수행하세요.

답변은 한국어로 제공하며, 정중하고 전문적인 톤을 유지하세요."""

# 변경된 부분: messages와 scratchpad를 하나의 MessagesPlaceholder로 통합
prompt = ChatPromptTemplate.from_messages([
    ("system", AGENT_PROMPT),
    MessagesPlaceholder(variable_name="messages"),  # 이전 대화 기록과 현재 입력을 포함
])
