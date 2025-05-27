from app.models import Report, db

class ReportDAO:
    def get_by_user(self, user_id):
        return Report.query.filter_by(user_id=user_id).all()

    def get(self, report_id):
        return Report.query.get(report_id)

    def create(self, **kwargs):
        report = Report(**kwargs)
        db.session.add(report)
        db.session.commit()
        return report

    def delete(self, report_id):
        report = self.get(report_id)
        if report:
            db.session.delete(report)
            db.session.commit()
            return True
        return False
