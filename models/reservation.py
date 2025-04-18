from datetime import datetime
from models.study_space import DateTimeRange

class Booking:
    _bookings = []  # In-memory storage

    def __init__(self, bookingID, student, room, timeSlot):
        self.bookingID = bookingID
        self.student = student
        self.room = room
        self.timeSlot = timeSlot if isinstance(timeSlot, DateTimeRange) else DateTimeRange(timeSlot['startTime'], timeSlot['endTime'])
        self.qrCode = f"QR_{bookingID}"
        self.status = "pending"
        self.createdAt = datetime.now()
        Booking._bookings.append(self)

    def confirm(self):
        self.status = "confirmed"
        self.room.updateStatus("in_use")
        from models.room_schedule import RoomSchedule
        schedule = RoomSchedule(
            scheduleID=str(len(RoomSchedule.all()) + 1),
            room=self.room,
            startTime=self.timeSlot.startTime,
            endTime=self.timeSlot.endTime,
            status=self.status
        )
        schedule.save()

    def cancel(self):
        self.status = "canceled"
        self.room.updateStatus("available")
        from models.room_schedule import RoomSchedule
        schedule = next((s for s in RoomSchedule.all() if s.room == self.room and s.startTime == self.timeSlot.startTime), None)
        if schedule:
            schedule.status = "canceled"

    def save(self):
        if self not in Booking._bookings:
            Booking._bookings.append(self)

    @staticmethod
    def all():
        return Booking._bookings