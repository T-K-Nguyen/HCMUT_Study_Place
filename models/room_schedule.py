from datetime import datetime
from models.study_space import DateTimeRange

class RoomSchedule:
    _schedules = []  # In-memory storage

    def __init__(self, scheduleID, room, startTime, endTime, status="pending"):
        self.scheduleID = scheduleID
        self.room = room
        self.startTime = startTime if isinstance(startTime, datetime) else datetime.strptime(startTime, '%Y-%m-%d %H:%M')
        self.endTime = endTime if isinstance(endTime, datetime) else datetime.strptime(endTime, '%Y-%m-%d %H:%M')
        self.status = status
        RoomSchedule._schedules.append(self)

    def conflictsWith(self, timeSlot):
        current = DateTimeRange(self.startTime, self.endTime)
        return current.overlaps(timeSlot) and self.status != "canceled"

    def save(self):
        if self not in RoomSchedule._schedules:
            RoomSchedule._schedules.append(self)

    @staticmethod
    def all():
        return RoomSchedule._schedules
