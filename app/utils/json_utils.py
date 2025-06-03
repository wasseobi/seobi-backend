import re

def extract_json_string(s: str) -> str:
    """문자열에서 JSON 형식의 문자열을 추출합니다.
    
    Args:
        s: JSON 문자열이 포함된 텍스트
        
    Returns:
        추출된 JSON 문자열
    """
    s = s.strip()
    if s.startswith("```json"):
        s = s[len("```json"):].strip()
    if s.startswith("```"):
        s = s[len("```"):].strip()
    if s.startswith("json"):
        s = s[4:].strip()
    match = re.search(r'({.*})', s, re.DOTALL)
    if match:
        return match.group(1)
    return s 