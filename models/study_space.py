from sqlalchemy import Column, Integer, String, ForeignKey, DateTime
from sqlalchemy.orm import relationship
from data.database import Base, SessionLocal
from datetime import datetime

class DateTimeRange(Base):
    __tablename__ = "datetime_ranges"

    id = Column(Integer, primary_key=True, index=True)
    startTime = Column(DateTime, nullable=False)
    endTime = Column(DateTime, nullable=False)

    def __init__(self, startTime, endTime):
        self.startTime = startTime
        self.endTime = endTime

    def to_string(self):
        return f"{self.startTime.strftime('%Y-%m-%d %H:%M')} - {self.endTime.strftime('%H:%M')}"

    def overlaps(self, other):
        return self.startTime < other.endTime and self.endTime > other.startTime


class Room(Base):
    __tablename__ = "rooms"

    roomID = Column(String, primary_key=True, index=True)  # Changed to String
    type = Column(String, nullable=False)
    capacity = Column(Integer, nullable=False)
    equipment = Column(String)  # Storing as JSON string
    status = Column(String, default="available")
    location = Column(String)
    timeSlot_id = Column(Integer, ForeignKey("datetime_ranges.id"), nullable=True)

    timeSlot = relationship("DateTimeRange")

    # def __init__(self, roomID, type, capacity, equipment=None, status="", location=""):
    #     self.roomID = roomID
    #     self.type = type
    #     self.capacity = capacity
    #     self.equipment = equipment or []
    #     self.status = status
    #     self.location = location
    #     Room._rooms.append(self)

    def getAvailability(self, timeSlot):
        if self.status != "available":
            return False
        if not self.timeSlot:
            return True  # Phòng chưa được đặt gì thì rảnh
        return not self.timeSlot.overlaps(timeSlot)



    def updateStatus(self, newStatus):
        self.status = newStatus
        db = SessionLocal()
        db.commit()
        db.close()

    def updateTimeSlot(self, timeSlot):
        self.timeSlot = timeSlot
        db = SessionLocal()
        db.commit()
        db.close()

    @classmethod
    def find_by_id(cls, room_id):
        db = SessionLocal()
        room = db.query(cls).filter(cls.roomID == room_id).first()
        db.close()
        return room

    @classmethod
    def all(cls):
        db = SessionLocal()
        rooms = db.query(cls).all()
        db.close()
        return rooms