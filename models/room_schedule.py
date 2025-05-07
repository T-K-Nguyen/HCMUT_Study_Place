# from datetime import datetime
# from models.study_space import DateTimeRange
#
# class RoomSchedule:
#     _schedules = []  # In-memory storage
#
#     def __init__(self, scheduleID, room, startTime, endTime, status="pending"):
#         self.scheduleID = scheduleID
#         self.room = room
#         self.startTime = startTime if isinstance(startTime, datetime) else datetime.strptime(startTime, '%Y-%m-%d %H:%M')
#         self.endTime = endTime if isinstance(endTime, datetime) else datetime.strptime(endTime, '%Y-%m-%d %H:%M')
#         self.status = status
#         RoomSchedule._schedules.append(self)
#
#     def conflictsWith(self, timeSlot):
#         current = DateTimeRange(self.startTime, self.endTime)
#         return current.overlaps(timeSlot) and self.status != "canceled"
#
#     def save(self):
#         if self not in RoomSchedule._schedules:
#             RoomSchedule._schedules.append(self)
#
#     @staticmethod
#     def all():
#         return RoomSchedule._schedules

from sqlalchemy import Column, Integer, String, ForeignKey, DateTime
from sqlalchemy.orm import relationship
from data.database import Base, SessionLocal
from models.study_space import DateTimeRange

class RoomSchedule(Base):
    __tablename__ = "room_schedules"

    scheduleID = Column(Integer, primary_key=True, index=True)
    room_id = Column(Integer, ForeignKey("rooms.roomID"))
    startTime = Column(DateTime)
    endTime = Column(DateTime)
    status = Column(String, default="pending")

    room = relationship("Room")

    def conflictsWith(self, timeSlot):
        current = DateTimeRange(self.startTime, self.endTime)
        return current.overlaps(timeSlot) and self.status != "canceled"

    def save(self):
        db = SessionLocal()
        db.add(self)
        db.commit()
        db.close()

    @classmethod
    def all(cls):
        db = SessionLocal()
        schedules = db.query(cls).all()
        db.close()
        return schedules