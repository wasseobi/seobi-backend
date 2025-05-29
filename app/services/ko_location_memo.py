from konlpy.tag import Okt
import re
from transformers import pipeline

PLACE_KEYWORDS = [
    '공원', '역', '회의실', '카페', '병원', '사옥', '집', '출구', '식당', '학교', '도서관', '센터', '호텔', '교회',
    '미술관', '박물관', '강당', '운동장', '캠퍼스', '온라인', '한강', '롯데월드', '서울숲', '광화문', '코엑스', '타워', '플라자'
]

MEMO_KEYWORDS = ['챙기', '준비', '지참', '꼭', '필요', '주의', '명령', '알림', '메모', '참고', '해야', '오라고', '가지고', '선물', '지시', '부탁']

# 기존 koNLPy 방식 (LLM/NER 보조용)
def extract_location(text):
    okt = Okt()
    nouns = okt.nouns(text)
    for noun in nouns:
        for keyword in PLACE_KEYWORDS:
            if keyword in noun or noun in keyword:
                return noun
    return None

def extract_location_ner(text):
    ner = pipeline("ner", model="klue/bert-base", aggregation_strategy="simple")
    results = ner(text)
    for r in results:
        if r['entity_group'] == 'LOC' or r['entity_group'] == 'POH':
            return r['word']
    return None

def extract_memo(text):
    sentences = re.split(r'[.,/그리고]', text)
    memos = []
    for sent in sentences:
        for keyword in MEMO_KEYWORDS:
            if keyword in sent:
                memos.append(sent.strip())
    return ', '.join(memos) if memos else None 