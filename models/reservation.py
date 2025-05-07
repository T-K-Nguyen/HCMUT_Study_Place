from sqlalchemy import Column, Integer, String, ForeignKey, DateTime
from sqlalchemy.orm import relationship
from data.database import Base, SessionLocal
from models.study_space import DateTimeRange
from datetime import datetime
import uuid

class Booking(Base):
    __tablename__ = "bookings"

    bookingID = Column(Integer, primary_key=True, index=True)
    student_id = Column(Integer, ForeignKey("students.userID"))
    room_id = Column(String, ForeignKey("rooms.roomID"))  # Changed to String
    timeSlot_id = Column(Integer, ForeignKey("datetime_ranges.id"))
    qrCode = Column(String)
    status = Column(String, default="pending")
    createdAt = Column(DateTime, default=datetime.now)

    student = relationship("Student", back_populates="bookings")
    room = relationship("Room")
    timeSlot = relationship("DateTimeRange")

    def __init__(self, bookingID, student, room, timeSlot):
        self.bookingID = bookingID
        self.student = student
        self.room = room
        self.timeSlot = timeSlot
        self.qrCode = str(uuid.uuid4())  # Generate QR code on creation
        self.status = "pending"

    def confirm(self):
        self.status = "confirmed"
        self.room.updateStatus("reserved")
        db = SessionLocal()
        db.commit()
        db.close()

    def cancel(self):
        self.status = "canceled"
        self.room.updateStatus("available")
        db = SessionLocal()
        db.commit()
        db.delete(self)
        db.close()

    def save(self):
        db = SessionLocal()
        db.add(self)
        db.commit()
        db.close()

    @classmethod
    def all(cls):
        db = SessionLocal()
        bookings = db.query(cls).all()
        db.close()
        return bookings