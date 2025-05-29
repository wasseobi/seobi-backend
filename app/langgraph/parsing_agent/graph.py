# 자연어 파싱 에이전트 그래프 scaffold

def start(input_data):
    print('[DEBUG][start] input:', input_data)  # TODO: 나중에 삭제
    # 그래프 시작점
    return input_data

def call_model(input_data):
    # LLM 호출 (stub)
    # TODO: 실제 LLM 연동
    return {**input_data,
            'llm_result': 'LLM 해석 결과',
            'title': '팀 미팅',
            'repeat': '매주',
            'start_at': None,
            'finish_at': None,
            'location': '회의실',
            'status': 'undone',
            'linked_service': ''}

def tool(input_data):
    print('[DEBUG][tool] input:', input_data)  # TODO: 나중에 삭제
    import re
    text = input_data.get('text', '')
    title = ''
    repeat = ''
    start_at = None
    finish_at = None
    location = ''
    status = 'undone'
    linked_service = ''
    memo = ''

    # 장소 추출 (예: '잠실에서')
    loc_match = re.search(r'([가-힣A-Za-z0-9]+)에서', text)
    if loc_match:
        location = loc_match.group(1)

    # title 추출: 행동 키워드만 남기고, 특수 패턴 반영 + 식사 패턴 보강
    TITLE_KEYWORDS = ['회의', '미팅', '면담', '식사', '산책', '보고', '상담', '면접', '발표', '세미나', '교육', '출장', '방문']
    EAT_PATTERNS = ['먹자', '먹쟤', '먹으러', '먹고', '먹기로', '먹으자', '먹을까', '먹으래', '먹쟤', '조지자', '조지쟤', '조지러', '조지기로', '조지자고', '조지자고 하더라']
    for kw in TITLE_KEYWORDS:
        if kw in text:
            title = kw
            # '출근하자마자 회의' 등 특수 패턴
            if '출근하자마자' in text and kw == '회의':
                title = '출근하자마자 회의'
            break
    else:
        # 식사 관련 패턴이 있으면 '식사 일정'으로
        if any(pat in text for pat in EAT_PATTERNS):
            title = '식사 일정'
        else:
            title = '일정'

    # 시간 파싱 고도화
    hour = None
    # '아홉시', '9시', '09시', '오전 아홉시', '오전 9시', '9시에' 등
    time_match = re.search(r'(오전|오후)? ?([0-9]{1,2}|[가-힣]{2,3})시', text)
    if time_match:
        h = time_match.group(2)
        # 한글 숫자 변환
        h = {'아홉':9, '열':10, '여덟':8, '일곱':7, '여섯':6, '다섯':5, '네':4, '세':3, '두':2, '한':1}.get(h, h)
        try:
            hour = int(h)
        except:
            hour = None
        # 오전/오후 처리
        if time_match.group(1) == '오후' and hour is not None and hour < 12:
            hour += 12
    elif '출근하자마자' in text:
        hour = 9  # 기본 출근 시간

    import datetime
    now = datetime.datetime.now()
    start_at = None
    if '내일' in text:
        start_at = now + datetime.timedelta(days=1)
    elif '오늘' in text:
        start_at = now
    if start_at and hour is not None:
        start_at = start_at.replace(hour=hour, minute=0, second=0, microsecond=0)
    elif start_at:
        start_at = start_at.replace(hour=10, minute=0, second=0, microsecond=0)

    # memo 추출: 품목+행동 패턴 우선 추출
    ITEMS = ['메로나', '우산', '피푸봉투', '출입증', '신분증', '도장', '서류', '간식', '음료', '노트북', '충전기']
    ACTIONS = ['챙기', '지참', '준비', '가져', '가지고', '꼭', '필수', '해오', '오라', '오래', '오라고', '해오라고', '해오래', '해오라더라', '해오라고 했다']
    candidates = re.split(r'[.,/그리고\n]', text)
    for sent in candidates:
        for item in ITEMS:
            if item in sent:
                for act in ACTIONS:
                    if act in sent:
                        # "메로나 챙겨오라더라" → "메로나 챙기기"
                        memo = f"{item} 챙기기"
                        break
                else:
                    # 품목만 있으면 "메로나 준비" 등으로 fallback
                    memo = f"{item} 준비"
                break
        if memo:
            break
    # 기존 키워드 방식도 병행(품목 패턴이 없을 때만)
    if not memo:
        MEMO_KEYWORDS = [
            '챙기', '준비', '지참', '신경', '주의', '필요', '확인', '알림', '메모', '참고', '감정', '기분', '엄수', '출입증', '지시', '부탁',
            '가져', '가지고', '꼭', '필수', '필히', '주의사항', '유의', '조심', '생각', '기억', '준수', '지켜', '준비물', '해야', '해야함', '해야 해', '해야돼', '해야 돼'
        ]
        for sent in candidates:
            for kw in MEMO_KEYWORDS:
                if kw in sent:
                    cleaned = re.sub(r'(이[라|라고]? ?함|이[라|라고]? 해|이[라|라고]? 함|이[라|라고]?함|이[라|라고]?함|이[라|라고]? 해요|이[라|라고]? 했음|이[라|라고]? 했어요)', '함', sent.strip())
                    cleaned = re.sub(r'\s+', ' ', cleaned)
                    cleaned = re.sub(r'해야 해(요)?', '해야 함', cleaned)
                    cleaned = re.sub(r'해야돼', '해야 함', cleaned)
                    cleaned = re.sub(r'해야 돼', '해야 함', cleaned)
                    cleaned = re.sub(r'해야함', '해야 함', cleaned)
                    cleaned = re.sub(r'\b함함\b', '함', cleaned)
                    memo = cleaned
                    break
            if memo:
                break
    else:
        memo = memo or ''

    # 반복 주기 추출
    if '매주' in text:
        repeat = '매주'
    elif '매월' in text:
        repeat = '매월'
    elif '격주' in text:
        repeat = '격주'
    elif any(day in text for day in ['월요일', '화요일', '수요일', '목요일', '금요일', '토요일', '일요일']):
        repeat = '특정요일'

    # 파싱 성공 기준(예시: 타이틀, 날짜, 장소 중 2개 이상 추출 시 성공)
    success_count = sum([bool(title), bool(start_at), bool(location)])
    if success_count >= 2:
        print('[DEBUG][tool] success:', {'title': title, 'repeat': repeat, 'start_at': start_at, 'location': location, 'memo': memo})  # TODO: 나중에 삭제
        return {**input_data,
                'parsing_result': '코드 파싱 성공',
                'title': title,
                'repeat': repeat,
                'start_at': start_at,
                'finish_at': finish_at,
                'location': location,
                'status': status,
                'linked_service': linked_service,
                'memo': memo,
                'end': True}
    else:
        print('[DEBUG][tool] fail, handoff needed')  # TODO: 나중에 삭제
        return {**input_data, 'parsing_result': '불확실', 'end': False}

def handoff(input_data):
    print('[DEBUG][handoff] input:', input_data)  # TODO: 나중에 삭제
    # LLM에게 title/memo를 자연어 의미 기반으로 요약 요청 (정규표현식/하드코딩 완전 제거)
    # TODO: 실제 LLM 연동 및 프롬프트 적용
    # title 프롬프트 예시:
    # "아래 일정을 한 줄로 요약해줘. 시간, 장소 등은 빼고, 핵심 행동/주제만 남겨줘. 예시) '로건이와 산책', '김부장 미팅', '삼겹살 회식'"
    # memo 프롬프트 예시:
    # "아래 일정에서 준비물, 신경쓸 것, 참고사항, 감정표현, 정보 등을 한국어로 가장 자연스럽고 간결하게 한 줄로 요약해줘. 예시) '피푸봉투 챙기기', '메로나 지참', '우산 챙기기'"
    # 실제 LLM 연동 예시 (pseudo-code):
    # title_summary = call_llm(title_prompt, input_data['text'])
    # memo_summary = call_llm(memo_prompt, input_data['text'])
    # return {**input_data, 'title': title_summary, 'memo': memo_summary, ...}
    # 현재는 임시로 'LLM 요약 결과' 반환
    return {**input_data,
            'handoff_result': 'LLM 추가 분석',
            'title': 'LLM 요약 결과',
            'memo': 'LLM 요약 결과',
            'end': False}

def end(input_data):
    print('[DEBUG][end] result:', input_data)  # TODO: 나중에 삭제
    # memo 한국어 문법 후처리: '~챙겨야 해 이라고함' → '챙겨야 함' 등
    import re
    memo = input_data.get('memo', '')
    if memo:
        memo = re.sub(r'(이[라|라고]? ?함|이[라|라고]? 해|이[라|라고]? 함|이[라|라고]?함|이[라|라고]?함|이[라|라고]? 해요|이[라|라고]? 했음|이[라|라고]? 했어요)', '함', memo)
        memo = re.sub(r'\s+', ' ', memo)
        memo = re.sub(r'해야 해(요)?', '해야 함', memo)
        memo = re.sub(r'해야돼', '해야 함', memo)
        memo = re.sub(r'해야 돼', '해야 함', memo)
        memo = re.sub(r'해야함', '해야 함', memo)
        memo = re.sub(r'\b함함\b', '함', memo)
    return {**input_data, 'memo': memo}

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