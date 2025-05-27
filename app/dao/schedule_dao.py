from app.models import Schedule, db

class ScheduleDAO:
    def get_by_user(self, user_id):
        return Schedule.query.filter_by(user_id=user_id).all()

    def get(self, schedule_id):
        return Schedule.query.get(schedule_id)

    def create(self, **kwargs):
        schedule = Schedule(**kwargs)
        db.session.add(schedule)
        db.session.commit()
        return schedule

    def delete(self, schedule_id):
        schedule = self.get(schedule_id)
        if schedule:
            db.session.delete(schedule)
            db.session.commit()
            return True
        return False
