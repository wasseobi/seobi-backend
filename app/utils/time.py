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