from datetime import datetime, timedelta, timezone
from zoneinfo import ZoneInfo

class TimeUtils:
    @staticmethod
    def get_timezone(tz_str):
        try:
            return ZoneInfo(tz_str)
        except Exception:
            return timezone.utc

    @staticmethod
    def to_local(dt, tz):
        if dt is None:
            return None
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return dt.astimezone(tz).isoformat()
    

    @staticmethod
    def get_today_range(tz):
        now = datetime.now(tz)
        start_of_today = now.replace(hour=0, minute=0, second=0, microsecond=0)
        start_of_tomorrow = start_of_today + timedelta(days=1)
        return start_of_today.astimezone(timezone.utc), start_of_tomorrow.astimezone(timezone.utc)

    @staticmethod
    def get_tomorrow_range(tz):
        now = datetime.now(tz)
        start_of_today = now.replace(hour=0, minute=0, second=0, microsecond=0)
        start_of_tomorrow = start_of_today + timedelta(days=1)
        start_of_day_after = start_of_today + timedelta(days=2)
        return start_of_tomorrow.astimezone(timezone.utc), start_of_day_after.astimezone(timezone.utc)

    @staticmethod
    def get_week_range(tz):
        """현재 주의 시작일과 종료일을 반환"""
        now = datetime.now(tz)
        start_of_today = now.replace(hour=0, minute=0, second=0, microsecond=0)
        
        # 월요일(0)을 기준으로 주의 시작일 계산
        days_since_monday = start_of_today.weekday()
        start_of_week = start_of_today - timedelta(days=days_since_monday)
        end_of_week = start_of_week + timedelta(days=7)
        
        return start_of_week.astimezone(timezone.utc), end_of_week.astimezone(timezone.utc)

    @staticmethod
    def get_next_week_range(tz):
        """다음 주의 시작일과 종료일을 반환"""
        now = datetime.now(tz)
        start_of_today = now.replace(hour=0, minute=0, second=0, microsecond=0)
        
        # 현재 주의 월요일 구하기
        days_since_monday = start_of_today.weekday()
        start_of_this_week = start_of_today - timedelta(days=days_since_monday)
        
        # 다음 주의 시작일과 종료일
        start_of_next_week = start_of_this_week + timedelta(days=7)
        end_of_next_week = start_of_next_week + timedelta(days=7)
        
        return start_of_next_week.astimezone(timezone.utc), end_of_next_week.astimezone(timezone.utc)

    @staticmethod
    def get_month_range(tz):
        """현재 월의 시작일과 종료일을 반환"""
        now = datetime.now(tz)
        start_of_month = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        
        # 다음 달의 1일을 구한 후, 1일에서 하루를 빼서 이번 달의 마지막 날을 구함
        if now.month == 12:
            next_month = now.replace(year=now.year + 1, month=1, day=1)
        else:
            next_month = now.replace(month=now.month + 1, day=1)
        
        end_of_month = next_month
        
        return start_of_month.astimezone(timezone.utc), end_of_month.astimezone(timezone.utc)

    @staticmethod
    def get_next_month_range(tz):
        """다음 월의 시작일과 종료일을 반환"""
        now = datetime.now(tz)
        
        # 다음 달의 시작일 계산
        if now.month == 12:
            start_of_next_month = now.replace(year=now.year + 1, month=1, day=1, 
                                            hour=0, minute=0, second=0, microsecond=0)
            end_of_next_month = start_of_next_month.replace(month=2, day=1)
        elif now.month == 11:
            start_of_next_month = now.replace(month=12, day=1,
                                            hour=0, minute=0, second=0, microsecond=0)
            end_of_next_month = start_of_next_month.replace(year=now.year + 1, month=1, day=1)
        else:
            start_of_next_month = now.replace(month=now.month + 1, day=1,
                                            hour=0, minute=0, second=0, microsecond=0)
            end_of_next_month = start_of_next_month.replace(month=now.month + 2, day=1)
        
        return start_of_next_month.astimezone(timezone.utc), end_of_next_month.astimezone(timezone.utc)

    @staticmethod
    def get_week_of_year(dt):
        """해당 날짜의 연도와 몇 번째 주인지 반환"""
        year = dt.year
        week = dt.isocalendar()[1]
        return year, week

    @staticmethod
    def get_month_of_year(dt):
        """해당 날짜의 연도와 월을 반환"""
        return dt.year, dt.month