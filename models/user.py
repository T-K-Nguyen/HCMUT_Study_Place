# from datetime import datetime
#
# class User:
#     _users = []  # In-memory storage
#
#     def __init__(self, userID, name, email, role):
#         self.userID = userID
#         self.name = name
#         self.email = email
#         self.role = role
#         self._logged_in = False
#         User._users.append(self)
#
#     def login(self):
#         self._logged_in = True
#         return True
#
#     def logout(self):
#         self._logged_in = False
#
#     @staticmethod
#     def find_by_id(user_id):
#         return next((user for user in User._users if user.userID == user_id), None)
#
#     @staticmethod
#     def all():
#         return User._users
#
#
# class Student(User):
#     def __init__(self, userID, name, email):
#         super().__init__(userID, name, email, role="student")
#         self.bookings = []  # List of Booking objects
#         self.notifications = []  # List of Notification objects
#
#     def searchRoom(self, criteria):
#         from models.study_space import Room
#         rooms = Room.all()
#         filtered = []
#         for room in rooms:
#             if criteria.get('type') and room.type != criteria['type']:
#                 continue
#             if criteria.get('capacity') and room.capacity < criteria['capacity']:
#                 continue
#             if criteria.get('equipment') and not all(equip in room.equipment for equip in criteria['equipment']):
#                 continue
#             if criteria.get('timeSlot'):
#                 availability = room.getAvailability(criteria['timeSlot'])
#                 if not availability:
#                     continue
#             filtered.append(room)
#         return filtered
#
#     def bookRoom(self, room, timeSlot):
#         from models.reservation import Booking
#         from models.study_space import DateTimeRange
#         if not room.getAvailability(timeSlot):
#             return None
#         booking = Booking(
#             bookingID=str(len(Booking.all()) + 1),
#             student=self,
#             room=room,
#             timeSlot=timeSlot
#         )
#         self.bookings.append(booking)
#         return booking
#
#     def cancelBooking(self, bookingID):
#         booking = next((b for b in self.bookings if b.bookingID == bookingID), None)
#         if booking:
#             booking.cancel()
#             self.bookings.remove(booking)
#             return True
#         return False
#
#     def checkIn(self, qrCode):
#         booking = next((b for b in self.bookings if b.qrCode == qrCode and b.status == "pending"), None)
#         if booking:
#             booking.confirm()
#             booking.room.updateStatus("in_use")
#             print(f"IoT: Devices activated for {booking.room.roomID}")
#             return True
#         return False
#
#     def receiveNotification(self, msg):
#         from models.notification import Notification
#         notification = Notification(
#             messageID=str(len(self.notifications) + 1),
#             recipient=self,
#             content=msg,
#             sendTime=datetime.now()
#         )
#         self.notifications.append(notification)
#         notification.send()
#
#     def rateRoom(self, roomID, stars, comment):
#         from models.rating import Rating
#         from models.study_space import Room
#         room = Room.find_by_id(roomID)
#         if not room:
#             return False
#         rating = Rating(
#             ratingID=str(len(Rating.all()) + 1),
#             student=self,
#             room=room,
#             stars=stars,
#             comment=comment
#         )
#         rating.save()
#         return True
#
#
# class Admin(User):
#     def __init__(self, userID, name, email):
#         super().__init__(userID, name, email, role="admin")
#
#     def viewReports(self):
#         from models.report import Report
#         return [report for report in Report.all() if report.generatedBy == self]
#
#     def manageRooms(self):
#         from models.study_space import Room
#         return Room.all()
#
#     def manageAccounts(self):
#         return User.all()
#
#     def viewRoomRatings(self, roomID):
#         from models.rating import Rating
#         from models.study_space import Room
#         room = Room.find_by_id(roomID)
#         if not room:
#             return []
#         return [rating for rating in Rating.all() if rating.room == room]

from sqlalchemy import Column, Integer, String, Boolean, ForeignKey
from sqlalchemy.orm import relationship
from data.database import Base, SessionLocal
from models.reservation import Booking
from models.notification import Notification
from werkzeug.security import generate_password_hash, check_password_hash

class User(Base):
    __tablename__ = "users"

    userID = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, nullable=False)
    name = Column(String, nullable=False)
    email = Column(String, unique=True, nullable=False)
    role = Column(String, nullable=False)
    password = Column(String, nullable=False)
    logged_in = Column(Boolean, default=False)

    def set_password(self, password):
        self.password = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password, password)

    def login(self):
        self.logged_in = True
        db = SessionLocal()
        db.commit()
        db.close()
        return True

    def logout(self):
        self.logged_in = False
        db = SessionLocal()
        db.commit()
        db.close()

    @classmethod
    def find_by_id(cls, user_id):
        db = SessionLocal()
        user = db.query(cls).filter(cls.userID == user_id).first()
        db.close()
        return user

    @classmethod
    def find_by_username(cls, username):
        db = SessionLocal()
        user = db.query(cls).filter(cls.username == username).first()
        db.close()
        return user

    @classmethod
    def all(cls):
        db = SessionLocal()
        users = db.query(cls).all()
        db.close()
        return users

class Student(User):
    __tablename__ = "students"

    userID = Column(Integer, ForeignKey("users.userID"), primary_key=True)
    bookings = relationship("Booking", back_populates="student", foreign_keys=[Booking.student_id])
    notifications = relationship("Notification", back_populates="recipient")

    def __init__(self, userID, username, name, email, password):
        super().__init__()
        self.userID = userID
        self.username = username
        self.name = name
        self.email = email
        self.role = "student"
        self.set_password(password)

    def searchRoom(self, criteria):
        from models.study_space import Room
        rooms = Room.all()
        filtered = []
        for room in rooms:
            if criteria.get('type') and room.type != criteria['type']:
                continue
            if criteria.get('capacity') and room.capacity < criteria['capacity']:
                continue
            if criteria.get('equipment') and not all(equip in room.equipment for equip in criteria['equipment']):
                continue
            if criteria.get('timeSlot'):
                availability = room.getAvailability(criteria['timeSlot'])
                if not availability:
                    continue
            filtered.append(room)
        return filtered

    def bookRoom(self, db, room, timeSlot):
        from models.reservation import Booking
        print("getavailability:", room.getAvailability(timeSlot))
        if not room.getAvailability(timeSlot):
            return None
        booking = Booking(student=self, room=room, timeSlot=timeSlot)
        db.add(booking)
        return booking

    def cancelBooking(self, bookingID):
        from models.reservation import Booking
        db = SessionLocal()
        booking = db.query(Booking).filter_by(bookingID=bookingID, student_id=self.userID).first()
        if booking:
            booking.cancel()
            db.delete(booking)
            db.commit()
        db.close()
        return bool(booking)

    def checkIn(self, qrCode):
        from models.reservation import Booking
        db = SessionLocal()
        booking = db.query(Booking).filter_by(qrCode=qrCode, student_id=self.userID, status="pending").first()
        if booking:
            booking.confirm()
            booking.room.updateStatus("in_use")
            print(f"IoT: Devices activated for {booking.room.roomID}")
            db.commit()
        db.close()
        return bool(booking)

    def receiveNotification(self, msg):
        notification = Notification(recipient=self, content=msg)
        db = SessionLocal()
        db.add(notification)
        db.commit()
        db.close()
        return notification

    def rateRoom(self, roomID, stars, comment):
        from models.rating import Rating
        from models.study_space import Room
        room = Room.find_by_id(roomID)
        if not room:
            return False
        rating = Rating(student=self, room=room, stars=stars, comment=comment)
        db = SessionLocal()
        db.add(rating)
        db.commit()
        db.close()
        return True

class Admin(User):
    __tablename__ = "admins"

    userID = Column(Integer, ForeignKey("users.userID"), primary_key=True)

    def __init__(self, userID, username, name, email, password):
        super().__init__()
        self.userID = userID
        self.username = username
        self.name = name
        self.email = email
        self.role = "admin"
        self.set_password(password)

    def viewReports(self):
        from models.report import Report
        db = SessionLocal()
        reports = db.query(Report).filter_by(generatedBy_id=self.userID).all()
        db.close()
        return reports

    def manageRooms(self):
        from models.study_space import Room
        return Room.all()

    def manageAccounts(self):
        return User.all()

    def viewRoomRatings(self, roomID):
        from models.rating import Rating
        from models.study_space import Room
        room = Room.find_by_id(roomID)
        if not room:
            return []
        db = SessionLocal()
        ratings = db.query(Rating).filter_by(room_id=room.roomID).all()
        db.close()
        return ratings
