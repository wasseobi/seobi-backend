from datetime import datetime, timezone, timedelta
import re

class TimeUtils:
    def __init__(self):
        self.kst = timezone(timedelta(hours=9))
        
        # Korean numbers for general use
        self.korean_numbers = {
            0: '영', 1: '일', 2: '이', 3: '삼', 4: '사', 5: '오',
            6: '육', 7: '칠', 8: '팔', 9: '구', 10: '십'
        }
        
        # Korean numbers for time units (시, 분)
        self.time_numbers = {
            0: '영', 1: '한', 2: '두', 3: '세', 4: '네', 5: '다섯',
            6: '여섯', 7: '일곱', 8: '여덟', 9: '아홉', 10: '열',
            11: '열한', 12: '열두'
        }

    def to_korean_number(self, n: int, is_time: bool = False) -> str:
        """Convert number to Korean text, with special handling for time units"""
        if n == 0:
            return self.korean_numbers[0]
        
        numbers = self.time_numbers if is_time else self.korean_numbers
        
        if n <= 12 and is_time:
            return numbers[n]
            
        result = ''
        if n >= 10:
            result += numbers[n // 10] + '십'
            n %= 10
        if n > 0:
            result += numbers[n]
        return result

    def to_korean_time(self, dt: datetime = None) -> str:
        """Convert datetime to Korean time format (오전/오후 시 분)"""
        if dt is None:
            dt = datetime.now(self.kst)
            
        hour = dt.hour
        minute = dt.minute
        
        period = "오전" if hour < 12 else "오후"
        hour = hour if hour <= 12 else hour - 12
        korean_hour = f"{self.to_korean_number(hour, True)}시"
        korean_minute = f"{self.to_korean_number(minute)}분"
        
        return f"{period} {korean_hour} {korean_minute}"

    def update_script_time(self, script: str) -> str:
        """Update the time part in a briefing script to current time"""
        # Match anything between 오전/오후 and 브리핑을
        time_pattern = r"((오전|오후).*?) 브리핑을"
        
        current_time = self.to_korean_time()
        
        # Replace only the time part while keeping '브리핑을'
        updated_script = re.sub(time_pattern, f"{current_time} 브리핑을", script)
        return updated_script 