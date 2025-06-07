import re

def decode_unicode_escapes(text: str) -> str:
    try:
        return text.encode('latin1').decode('unicode_escape')
    except Exception:
        return text

def clean_text(text: str) -> str:
    if not text:
        return ''
    if isinstance(text, bytes):
        try:
            text = text.decode('utf-8', errors='replace')
        except Exception:
            text = str(text)

    text = text.replace('\n', ' ')
    text = text.replace('\n\n', ' ')
    text = re.sub(r'\\n', ' ', text)
    text = re.sub(r'!\[.*?\]\(.*?\)', '', text)
    text = re.sub(r'!\(.*?\)', '', text)
    text = re.sub(r'\[.*?\]\(.*?\)', '', text)
    text = re.sub(r'<.*?>', '', text)
    text = re.sub(r'\.\s*(png|jpg|jpeg|gif|svg)', '', text, flags=re.IGNORECASE)
    text = re.sub(r'[\*\#>`\[\]_\~]+', '', text)
    text = re.sub(r'\s+', ' ', text)
    return decode_unicode_escapes(text.strip())