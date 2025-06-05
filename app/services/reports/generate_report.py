from app.services.reports.summarize_report import SummarizeReport
from app.services.interest_service import InterestService
from app.services.schedule_service import ScheduleService

from app.utils.time import TimeUtils

class GenerateReport:
    def __init__(self):
        from app.services.reports.daily.generate_daily_report import GenerateDailyReport
        from app.services.reports.weekly.generate_weekly_report import GenerateWeeklyReport
        from app.services.reports.monthly.generate_monthly_report import GenerateMonthlyReport
        self.summarizer = SummarizeReport()
        self.daily_report_generator = GenerateDailyReport()
        self.weekly_report_generator = GenerateWeeklyReport()
        self.monthly_report_generator = GenerateMonthlyReport()
        self.interest_service = InterestService()
        self.schedule_service = ScheduleService()

    def format_report_content(self, user_id, tz=None, report_type='daily'):
        if tz is None:
            tz = TimeUtils.get_timezone("UTC")
            
        if report_type == 'daily':
            markdown = self.daily_report_generator.generate_daily_report(user_id, tz)
            script = self.daily_report_generator.generate_daily_report_script(user_id, markdown, tz)
        elif report_type == 'weekly':
            markdown = self.weekly_report_generator.generate_weekly_report(user_id, tz)
            script = self.weekly_report_generator.generate_weekly_report_script(user_id, markdown, tz)
        elif report_type == 'monthly':
            markdown = self.monthly_report_generator.generate_monthly_report(user_id, tz)
            script = self.monthly_report_generator.generate_monthly_report_script(user_id, markdown, tz)
        else:
            raise ValueError(f"지원하지 않는 report_type: {report_type}")
            
        return {
            "text": markdown,
            "script": script
        }