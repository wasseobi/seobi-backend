from app.dao.schedule_dao import ScheduleDAO

class ScheduleService:
    def __init__(self):
        self.dao = ScheduleDAO()

    def get_user_schedules(self, user_id):
        return self.dao.get_by_user(user_id)

    def get_schedule(self, schedule_id):
        return self.dao.get(schedule_id)

    def create_schedule(self, data):
        return self.dao.create(**data)

    def delete_schedule(self, schedule_id):
        return self.dao.delete(schedule_id)
