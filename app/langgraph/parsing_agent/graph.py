# 자연어 파싱 에이전트 그래프 scaffold
from .nodes import start, tool, handoff, end, validate

def call_model(input_data):
    # (더 이상 사용하지 않거나, 실제 LLM 연동 시에만 사용)
    # TODO: 필요시 실제 LLM 연동 구현
    return input_data

def validate(input_data):
    print('[DEBUG][validate] input:', input_data)  # TODO: 나중에 삭제
    # LLM 검증 노드 (stub)
    # TODO: 실제 LLM 연동 및 평가 기준 구현
    # 예시 프롬프트:
    # "아래 일정 정보가 충분히 명확한가요? title은 반드시 있어야 하며, start_at, repeat, memo는 NULL이어도 괜찮지만,
    # NULL인 경우 그 이유가 자연스러운지 반드시 검토해서 OK/NO로 답변하세요."
    # 실제 LLM 연동 예시 (pseudo-code):
    # response = call_llm(prompt, input_data)
    # if response == 'OK':
    #     satisfied = True
    # else:
    #     satisfied = False
    # 현재는 임시로 title만 있으면 만족, 나머지는 LLM이 맥락적으로 판단한다고 가정
    if input_data.get('title'):
        print('[DEBUG][validate] 만족')  # TODO: 나중에 삭제
        return {**input_data, 'validation': '만족', 'satisfied': True}
    else:
        print('[DEBUG][validate] 불만족')  # TODO: 나중에 삭제
        return {**input_data, 'validation': '불만족', 'satisfied': False}


def parsing_agent(input_data, max_retry=5):
    data = start(input_data)
    retry_count = 0
    while retry_count < max_retry:
        data = tool(data)
        data = validate(data)
        if data.get('satisfied'):
            break
        # 불만족 시 LLM handoff로 재파싱
        data = handoff(data)
        data = validate(data)
        if data.get('satisfied'):
            break
        retry_count += 1
    result = end(data)
    return result 