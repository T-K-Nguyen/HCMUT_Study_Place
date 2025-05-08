# from datetime import datetime
#
# class Rating:
#     _ratings = []  # In-memory storage
#
#     def __init__(self, ratingID, student, room, stars, comment):
#         self.ratingID = ratingID
#         self.student = student
#         self.room = room
#         self.stars = stars
#         self.comment = comment
#         self.timestamp = datetime.now()
#         Rating._ratings.append(self)
#
#     def save(self):
#         if self not in Rating._ratings:
#             Rating._ratings.append(self)
#
#     @staticmethod
#     def all():
#         return Rating._ratings

from sqlalchemy import Column, Integer, String, ForeignKey, DateTime
from sqlalchemy.orm import relationship
from data.database import Base, SessionLocal

class Rating(Base):
    __tablename__ = "ratings"

    ratingID = Column(Integer, primary_key=True, index=True)
    student_id = Column(Integer, ForeignKey("students.userID"))
    room_id = Column(Integer, ForeignKey("rooms.roomID"))
    stars = Column(Integer)
    comment = Column(String)
    timestamp = Column(DateTime, default=DateTime.now)

    student = relationship("Student")
    room = relationship("Room")

    def save(self):
        db = SessionLocal()
        db.add(self)
        db.commit()
        db.close()

    @classmethod
    def all(cls):
        db = SessionLocal()
        ratings = db.query(cls).all()
        db.close()
        return ratings