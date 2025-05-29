# 자연어 파싱 에이전트 그래프 scaffold

def start(input_data):
    # 그래프 시작점
    return input_data

def call_model(input_data):
    # (더 이상 사용하지 않거나, 실제 LLM 연동 시에만 사용)
    # TODO: 필요시 실제 LLM 연동 구현
    return input_data

def tool(input_data):
    print('[DEBUG][tool] input:', input_data)  # TODO: 나중에 삭제
    import re
    text = input_data.get('text', '')
    repeat = ''
    start_at = None
    finish_at = None
    location = ''
    status = 'undone'
    linked_service = ''
    # 장소 추출 (예: '잠실에서')
    loc_match = re.search(r'([가-힣A-Za-z0-9]+)에서', text)
    if loc_match:
        location = loc_match.group(1)
    # 시간 표현 24시간제로 전처리
    text_proc = text
    def replace_time(match):
        period = match.group(1)
        h = match.group(2)
        h_num = {'아홉':9, '열':10, '여덟':8, '일곱':7, '여섯':6, '다섯':5, '네':4, '세':3, '두':2, '한':1, '열두':12, '열한':11}.get(h, h)
        try:
            h_num = int(h_num)
        except:
            return match.group(0)
        if period in ['오후', '저녁', '밤']:
            if h_num < 12:
                h_num += 12
        elif period in ['오전', '아침'] and h_num == 12:
            h_num = 0
        return f'{h_num}시'
    text_proc = re.sub(r'(오전|오후|저녁|밤|아침) ?([0-9]{1,2}|[가-힣]{2,3})시', replace_time, text_proc)
    # 시간 추출 (24시간제 변환 후)
    hour = None
    time_match = re.search(r'([0-9]{1,2})시', text_proc)
    if time_match:
        try:
            hour = int(time_match.group(1))
        except:
            hour = None
    elif '출근하자마자' in text_proc:
        hour = 9
    import datetime
    now = datetime.datetime.now()
    # 날짜 계산: '내일' 없으면 기본적으로 오늘로 처리
    if '내일' in text_proc:
        start_at = now + datetime.timedelta(days=1)
    else:
        start_at = now
    if start_at and hour is not None:
        start_at = start_at.replace(hour=hour, minute=0, second=0, microsecond=0)
    elif start_at:
        start_at = start_at.replace(hour=10, minute=0, second=0, microsecond=0)
    # 반복 주기 추출
    if '매주' in text:
        repeat = '매주'
    elif '매월' in text:
        repeat = '매월'
    elif '격주' in text:
        repeat = '격주'
    elif any(day in text for day in ['월요일', '화요일', '수요일', '목요일', '금요일', '토요일', '일요일']):
        repeat = '특정요일'
    # title, memo는 LLM에 위임
    return {**input_data,
            'parsing_result': '정형 정보 추출',
            'title': '',
            'repeat': repeat,
            'start_at': start_at,
            'finish_at': finish_at,
            'location': location,
            'status': status,
            'linked_service': linked_service,
            'memo': '',
            'end': False}

from app.utils.openai_client import init_langchain_llm

def handoff(input_data):
    print('[DEBUG][handoff] input:', input_data)  # TODO: 나중에 삭제
    llm = init_langchain_llm()
    title_prompt = (
        "아래 일정을 한 줄로 요약해줘. 시간, 장소 등은 빼고, 핵심 행동/주제만 남겨줘. "
        "예시) '로건이와 산책', '김부장 미팅', '삼겹살 회식', '짬뽕 식사'"
    )
    memo_prompt = (
        "아래 일정에서 준비물, 신경쓸 것, 참고사항, 감정표현, 정보 등을 한 줄로 요약해줘. "
        "예시) '피푸봉투 챙기기', '메로나 지참', '우산 챙기기'"
    )
    text = input_data['text']
    title_resp = llm.invoke([{"role": "user", "content": f"{title_prompt}\n{text}"}])
    memo_resp = llm.invoke([{"role": "user", "content": f"{memo_prompt}\n{text}"}])
    title = getattr(title_resp, 'content', str(title_resp))
    memo = getattr(memo_resp, 'content', str(memo_resp))
    # 따옴표로 감싸진 경우 반복적으로 제거
    import re
    def strip_quotes(s):
        if isinstance(s, str):
            while True:
                new_s = re.sub(r"^[\'\"](.*)[\'\"]$", r"\1", s.strip())
                if new_s == s:
                    break
                s = new_s
            return s
        return s
    title = strip_quotes(title)
    memo = strip_quotes(memo)
    return {**input_data,
            'handoff_result': 'LLM 추가 분석',
            'title': title,
            'memo': memo,
            'end': False}

def end(input_data):
    print('[DEBUG][end] result:', input_data)  # TODO: 나중에 삭제
    # memo 한국어 문법 후처리: '~챙겨야 해 이라고함' → '챙겨야 함' 등
    memo = input_data.get('memo', '')
    title = input_data.get('title', '')
    if memo:
        import re
        memo = re.sub(r'(이[라|라고]? ?함|이[라|라고]? 해|이[라|라고]? 함|이[라|라고]?함|이[라|라고]?함|이[라|라고]? 해요|이[라|라고]? 했음|이[라|라고]? 했어요)', '함', memo)
        memo = re.sub(r'\s+', ' ', memo)
        memo = re.sub(r'해야 해(요)?', '해야 함', memo)
        memo = re.sub(r'해야돼', '해야 함', memo)
        memo = re.sub(r'해야 돼', '해야 함', memo)
        memo = re.sub(r'해야함', '해야 함', memo)
        memo = re.sub(r'\b함함\b', '함', memo)
        # 따옴표로 감싸진 경우 반복적으로 제거
        while True:
            new_memo = re.sub(r"^[\'\"](.*)[\'\"]$", r"\1", memo.strip())
            if new_memo == memo:
                break
            memo = new_memo
    if title:
        while True:
            new_title = re.sub(r"^[\'\"](.*)[\'\"]$", r"\1", title.strip())
            if new_title == title:
                break
            title = new_title
    return {**input_data, 'memo': memo, 'title': title}

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

# 그래프 연결 예시 (실제 langgraph 등으로 연결 필요)
def parsing_agent(input_data, max_retry=3):
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