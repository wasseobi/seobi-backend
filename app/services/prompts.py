# 관심사 추출 프롬프트
EXTRACT_KEYWORDS_SYSTEM_PROMPT = (
    "아래 메시지 리스트를 참고해서 사용자의 관심 키워드를 추출하고, "
    "각 키워드가 어떤 message_id에서 추출됐는지 반드시 JSON 배열 형태로 반환하세요. "
    "출력 예시: [{\"keyword\": \"국내여행\", \"message_ids\": [\"c7da6b58-3700-469d-9fd7-0b0f5b78571b\", \"55460f94-f1c2-423b-a3e3-4f9011f4633c\"]}...]"
    "\n각 message_ids는 문자열 리스트로, 키워드별로 연관된 message_id만 포함해야 합니다. "
    "불필요한 설명 없이 JSON 데이터만 출력하세요."
)


def get_interest_user_prompt(message_list):
    """
    message_list: [{'id': '...', 'content': '...'}, ...]
    """
    joined = "\n".join(
        f"- id: {m['id']}, content: {m['content']}" for m in message_list)
    return (
        "아래 메시지 리스트를 참고해서 사용자의 관심 키워드와, 각 키워드가 어떤 message_id에서 추출됐는지 JSON 형태로 반환해줘.\n"
        "메시지 리스트:\n" + joined
    )


# 세션 요약 프롬프트
SESSION_SUMMARY_SYSTEM_PROMPT = (
    "다음 대화 전체를 바탕으로 세션의 제목과 설명을 생성해주세요. 제목은 20자 이내, 설명은 100자 이내로 작성하고, 응답은 JSON 형식으로 'title'과 'description' 키를 포함해야 합니다."
)

SESSION_SUMMARY_USER_PROMPT = ("다음 대화를 바탕으로 세션의 제목과 설명을 생성해주세요: \n\n")
