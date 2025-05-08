from sqlalchemy import Column, Integer, String, ForeignKey, DateTime
from sqlalchemy.orm import relationship
from data.database import Base, SessionLocal
from models.study_space import DateTimeRange

class RoomSchedule(Base):
    __tablename__ = "room_schedules"

    scheduleID = Column(Integer, primary_key=True, index=True)
    room_id = Column(String, ForeignKey("rooms.roomID"))  # Changed to String to match Room.roomID
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