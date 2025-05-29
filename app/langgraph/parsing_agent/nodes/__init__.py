import logging
from app.utils.openai_client import init_langchain_llm
from app.utils.message.parser import strip_quotes
from app.utils.prompt.parse_prompts import title_prompt, memo_prompt

logging.basicConfig(level=logging.DEBUG)

def start(input_data):
    # 그래프 시작점
    return input_data

def tool(input_data):
    import re
    text = input_data.get('text', '')
    logging.debug(f'[tool][input text]: {text}')
    repeat = ''
    start_at = None
    finish_at = None
    location = ''
    status = 'undone'
    linked_service = ''
    memo_reason = ''
    # 장소 추출 (예: '잠실에서')
    loc_match = re.search(r'([가-힣A-Za-z0-9]+)에서', text)
    if loc_match:
        location = loc_match.group(1)
    # 시간 표현 24시간제로 전처리
    text_proc = text
    logging.debug(f'[tool][before replace_time]: {text_proc}')
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
    # 추가: 접두사 없는 한글 시각도 변환
    def replace_korean_hour(match):
        h = match.group(1)
        h_num = {'아홉':9, '열':10, '여덟':8, '일곱':7, '여섯':6, '다섯':5, '네':4, '세':3, '두':2, '한':1, '열두':12, '열한':11}.get(h, h)
        try:
            h_num = int(h_num)
        except:
            return match.group(0)
        return f'{h_num}시'
    text_proc = re.sub(r'([가-힣]{2,3})시', replace_korean_hour, text_proc)
    logging.debug(f'[tool][after replace_time]: {text_proc}')
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
    # 맥락 기반 보정: 점심/식사/런치 등 키워드가 있으면 12~14시로 보정
    if any(kw in text for kw in ['점심', '식사', '런치']):
        if hour is None or hour in [12, 1, 2, 3]:
            # 두시, 한시, 세시 등은 점심 맥락이면 오후로 보정
            if hour == 1:
                hour = 13
                memo_reason = '점심/식사 맥락에서 1시는 오후 1시로 보정함.'
            elif hour == 2:
                hour = 14
                memo_reason = '점심/식사 맥락에서 2시는 오후 2시로 보정함.'
            elif hour == 3:
                hour = 13 # 보수적으로 13시(1시)로 보정
                memo_reason = '점심/식사 맥락에서 3시는 오후 1시로 보정함.'
            elif hour == 12 or hour is None:
                hour = 12
                memo_reason = '점심/식사 맥락에서 12시로 보정함.'
    # 불확실한 경우(오전/오후 명시X, 1~6시 등)에는 오후로 보정
    elif hour is not None and hour >= 1 and hour <= 6 and not any(p in text for p in ['오전', '아침']):
        hour += 12
        memo_reason = f'오전/오후 미지정, {hour-12}시를 오후 {hour}시로 보정함.'
    logging.debug(f'[tool][hour]: {hour}')
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
    logging.debug(f'[tool][start_at]: {start_at}')
    # 반복 주기 추출
    if '매주' in text:
        repeat = '매주'
    elif '매월' in text:
        repeat = '매월'
    elif '매달' in text:
        repeat = '매월'
    elif '격주' in text:
        repeat = '격주'
    elif '격월' in text:
        repeat = '격월'
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
            'memo': memo_reason,
            'end': False}

def handoff(input_data):
    llm = init_langchain_llm()
    text = input_data['text']
    title_resp = llm.invoke([{"role": "user", "content": f"{title_prompt}\n{text}"}], max_tokens=20)
    memo_resp = llm.invoke([{"role": "user", "content": f"{memo_prompt}\n{text}"}], max_tokens=30)
    title = getattr(title_resp, 'content', str(title_resp))
    memo = getattr(memo_resp, 'content', str(memo_resp))
    title = strip_quotes(title)
    memo = strip_quotes(memo)
    # Fallback: title이 비어있으면 원본 텍스트 일부라도 사용
    if not title.strip():
        title = text[:20] + '...'
        memo = (memo or '') + ' [AI가 제목을 추출하지 못해 원문 일부를 제목으로 사용함]'
    # 후처리: title이 원문 전체이거나 너무 길면, 핵심 단어만 추출
    if len(title) > 15 or title.strip() == text.strip():
        import re
        # 대표 키워드 후보
        keywords = ['파티', '모임', '회식', '회의', '식사', '발표', '강연', '운동', '산책', '공연', '관람', '스터디', '캠핑', '여행', '봉사', '야유회', '등산', '피크닉', '바베큐', '홈파티']
        for kw in keywords:
            if kw in text:
                title = kw
                break
    return {**input_data,
            'handoff_result': 'LLM 추가 분석',
            'title': title,
            'memo': memo,
            'end': False}

def end(input_data):
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
        memo = strip_quotes(memo)
    if title:
        title = strip_quotes(title)
    return {**input_data, 'memo': memo, 'title': title}

def validate(input_data):
    # LLM 검증 노드 (stub)
    if input_data.get('title'):
        return {**input_data, 'validation': '만족', 'satisfied': True}
    else:
        return {**input_data, 'validation': '불만족', 'satisfied': False} 