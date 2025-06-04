# 관심사 추출 프롬프트
EXTRACT_KEYWORDS_SYSTEM_PROMPT = (
    "아래 메시지 리스트를 참고해서 사용자의 관심 키워드를 추출하고, "
    "각 키워드가 어떤 message_id에서 추출됐는지와 중요도(importance, 0~1 float)를 반드시 JSON 배열 형태로 반환하세요. "
    "출력 예시: [{\"keyword\": \"국내여행\", \"importance\": 0.92, \"message_ids\": [\"c7da6b58-3700-469d-9fd7-0b0f5b78571b\", \"55460f94-f1c2-423b-a3e3-4f9011f4633c\"]}]"
    "\n각 message_ids는 문자열 리스트로, 키워드별로 연관된 message_id만 포함해야 합니다. "
    "importance는 해당 키워드가 사용자 관심사에서 차지하는 의미/비중을 0~1 사이 실수로 평가해 주세요. "
    "특히, 새로 추출된 키워드가 기존 키워드 리스트와 비슷할수록 importance를 높게 평가하세요. "
    "불필요한 설명 없이 JSON 데이터만 출력하세요."
)


def get_interest_user_prompt(message_list, user_keywords=None):
    """
    message_list: [{'id': '...', 'content': '...'}, ...]
    user_keywords: ["키워드1", "키워드2", ...] (optional)
    """
    joined = "\n".join(
        f"- id: {m['id']}, content: {m['content']}" for m in message_list)
    prompt = (
        "아래 메시지 리스트를 참고해서 사용자의 관심 키워드와, 각 키워드가 어떤 message_id에서 추출됐는지, 그리고 중요도(importance, 0~1 float)를 JSON 형태로 반환해줘.\n"
        "중요도는 해당 키워드가 사용자 관심사에서 차지하는 의미/비중을 0~1 사이 실수로 평가해줘.\n"
    )
    if user_keywords:
        prompt += (
            f"\n참고: 사용자의 기존 관심 키워드 리스트는 다음과 같아. 새로 추출된 키워드가 이 리스트와 비슷할수록 중요도를 높게 평가해줘.\n기존 키워드: {', '.join(user_keywords)}\n"
        )
    prompt += "메시지 리스트:\n" + joined
    return prompt


# 세션 요약 프롬프트
SESSION_SUMMARY_SYSTEM_PROMPT = (
    "다음 대화 전체를 바탕으로 세션의 제목과 설명을 생성해주세요. 제목은 20자 이내, 설명은 100자 이내로 작성하고, 응답은 JSON 형식으로 'title'과 'description' 키를 포함해야 합니다."
)

SESSION_SUMMARY_USER_PROMPT = ("다음 대화를 바탕으로 세션의 제목과 설명을 생성해주세요: \n\n")

INSIGHT_ARTICLE_SYSTEM_PROMPT = (
    "다음 대화 내용을 바탕으로 사용자의 관심사에 맞는 인사이트 아티클을 작성해주세요. "
    "아티클은 사용자의 상위 3개 관심사를 반영하고, 제목과 내용을 포함해야 합니다. "
    "제목은 50자 이내로 작성하고, 내용은 500자 이상이어야 합니다. "
    "응답은 JSON 형식으로 'title'과 'content' 키를 포함해야 합니다."
)

USER_MEMORY_SYSTEM_PROMPT = ("당신은 사용자의 장기기억을 생성 및 관리하는 AI입니다.\n\n"
        "아래는 세 가지 정보입니다:\n"
        "- [기존 장기기억]: 현재까지 저장된 사용자 정보\n"
        "- [최근 대화 요약]: 최근 대화의 핵심 내용 요약\n"
        "- [최근 메시지]: 사용자의 가장 최근 발화 내용\n\n"
        "이 세 정보를 종합해 **사용자의 장기기억(사용자의 주요 관심사, 선호도, 취향)을 업데이트** 해주세요.\n\n"
        "작성 기준은 다음과 같습니다:\n"
        "1. 중복된 정보는 제거하고, 더 구체적인 내용으로 갱신하세요.\n"
        "2. 불필요하거나 일시적인 내용은 포함하지 마세요 (예: 감탄사, 잡담, 일회성 요청 등).\n"
        "3. 정보 간 맥락을 고려하여 정리하고, 핵심 사실만 명확하게 정제하세요.\n"
        "4. 기존 장기기억의 구조를 유지하면서 필요한 부분만 보완하거나 교체하세요.\n"
        "5. 출력은 평문 텍스트로, 항목별 줄바꿈을 유지하세요.")