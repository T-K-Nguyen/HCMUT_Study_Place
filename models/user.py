from datetime import datetime

class User:
    _users = []  # In-memory storage

    def __init__(self, userID, name, email, role):
        self.userID = userID
        self.name = name
        self.email = email
        self.role = role
        self._logged_in = False
        User._users.append(self)

    def login(self):
        self._logged_in = True
        return True

    def logout(self):
        self._logged_in = False

    @staticmethod
    def find_by_id(user_id):
        return next((user for user in User._users if user.userID == user_id), None)

    @staticmethod
    def all():
        return User._users


class Student(User):
    def __init__(self, userID, name, email):
        super().__init__(userID, name, email, role="student")
        self.bookings = []  # List of Booking objects
        self.notifications = []  # List of Notification objects

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

    def bookRoom(self, room, timeSlot):
        from models.reservation import Booking
        from models.study_space import DateTimeRange
        if not room.getAvailability(timeSlot):
            return None
        booking = Booking(
            bookingID=str(len(Booking.all()) + 1),
            student=self,
            room=room,
            timeSlot=timeSlot
        )
        self.bookings.append(booking)
        return booking

    def cancelBooking(self, bookingID):
        booking = next((b for b in self.bookings if b.bookingID == bookingID), None)
        if booking:
            booking.cancel()
            self.bookings.remove(booking)
            return True
        return False

    def checkIn(self, qrCode):
        booking = next((b for b in self.bookings if b.qrCode == qrCode and b.status == "pending"), None)
        if booking:
            booking.confirm()
            booking.room.updateStatus("in_use")
            print(f"IoT: Devices activated for {booking.room.roomID}")
            return True
        return False

    def receiveNotification(self, msg):
        from models.notification import Notification
        notification = Notification(
            messageID=str(len(self.notifications) + 1),
            recipient=self,
            content=msg,
            sendTime=datetime.now()
        )
        self.notifications.append(notification)
        notification.send()

    def rateRoom(self, roomID, stars, comment):
        from models.rating import Rating
        from models.study_space import Room
        room = Room.find_by_id(roomID)
        if not room:
            return False
        rating = Rating(
            ratingID=str(len(Rating.all()) + 1),
            student=self,
            room=room,
            stars=stars,
            comment=comment
        )
        rating.save()
        return True


class Admin(User):
    def __init__(self, userID, name, email):
        super().__init__(userID, name, email, role="admin")

    def viewReports(self):
        from models.report import Report
        return [report for report in Report.all() if report.generatedBy == self]

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
        return [rating for rating in Rating.all() if rating.room == room]