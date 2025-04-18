from datetime import datetime

class DateTimeRange:
    def __init__(self, startTime, endTime):
        self.startTime = datetime.strptime(startTime, '%Y-%m-%d %H:%M') if isinstance(startTime, str) else startTime
        self.endTime = datetime.strptime(endTime, '%Y-%m-%d %H:%M') if isinstance(endTime, str) else endTime

    def overlaps(self, other):
        return self.startTime < other.endTime and self.endTime > other.startTime

    def __str__(self):
        return f"{self.startTime.strftime('%Y-%m-%d %H:%M')} - {self.endTime.strftime('%Y-%m-%d %H:%M')}"


class Room:
    _rooms = []  # In-memory storage

    def __init__(self, roomID, type, capacity, equipment=None, status="available", location=""):
        self.roomID = roomID
        self.type = type
        self.capacity = capacity
        self.equipment = equipment or []
        self.status = status
        self.location = location
        Room._rooms.append(self)

    def updateStatus(self, newStatus):
        self.status = newStatus

    def getAvailability(self, timeRange):
        from models.room_schedule import RoomSchedule
        schedules = [s for s in RoomSchedule.all() if s.room == self]
        for schedule in schedules:
            schedule_time = DateTimeRange(schedule.startTime, schedule.endTime)
            if schedule_time.overlaps(timeRange) and schedule.status != "canceled":
                return False
        return True

    def getAverageRating(self):
        from models.rating import Rating
        ratings = [r for r in Rating.all() if r.room == self]
        if not ratings:
            return 0.0
        return sum(r.stars for r in ratings) / len(ratings)

    @staticmethod
    def find_by_id(room_id):
        return next((room for room in Room._rooms if room.roomID == room_id), None)

    @staticmethod
    def all():
        return Room._rooms