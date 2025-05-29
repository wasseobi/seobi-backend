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