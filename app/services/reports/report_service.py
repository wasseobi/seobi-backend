from app.dao.report_dao import ReportDAO

class ReportService:
    def __init__(self):
        self.dao = ReportDAO()

    def get_user_reports(self, user_id):
        return self.dao.get_by_user(user_id)

    def get_report(self, report_id):
        return self.dao.get(report_id)

    def create_report(self, data):
        return self.dao.create(**data)

    def delete_report(self, report_id):
        return self.dao.delete(report_id)