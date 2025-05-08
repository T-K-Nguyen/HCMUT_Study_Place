# from datetime import datetime
# import json
#
#
# class DateTimeRange:
#     def __init__(self, startTime, endTime):
#         self.startTime = datetime.strptime(startTime, '%Y-%m-%d %H:%M') if isinstance(startTime, str) else startTime
#         self.endTime = datetime.strptime(endTime, '%Y-%m-%d %H:%M') if isinstance(endTime, str) else endTime
#
#     def overlaps(self, other):
#         return self.startTime < other.endTime and self.endTime > other.startTime
#
#     def __str__(self):
#         return f"{self.startTime.strftime('%Y-%m-%d %H:%M')} - {self.endTime.strftime('%Y-%m-%d %H:%M')}"
#
#     def to_dict(self):
#         return {
#             'startTime': self.startTime.strftime('%Y-%m-%d %H:%M'),
#             'endTime': self.endTime.strftime('%Y-%m-%d %H:%M')
#         }
#
#
# class Room:
#     _rooms = []  # In-memory storage
#     _data_file = 'data/spaces.json'  # Path to the JSON file
#
#     def __init__(self, roomID, type, capacity, equipment=None, status="available", location="", timeSlot=None):
#
#         self.roomID = roomID
#         self.type = type
#         self.capacity = capacity
#         self.equipment = equipment or []
#         self.status = status
#         self.location = location
#         self.timeSlot = timeSlot
#         # Check for duplicate roomID before creating a new room
#         if self.find_by_id(roomID):
#             return
#         Room._rooms.append(self)
#         self.save_to_file()  # Save to file whenever a new room is created
#
#     def updateType(self, newType):
#         self.type = newType
#         self.save_to_file()  # Save to file whenever the status is updated
#     def updateStatus(self, newStatus):
#         self.status = newStatus
#         self.save_to_file()  # Save to file whenever the status is updated
#     def updateCapacity(self, newcapacity):
#         self.capacity = newcapacity
#         self.save_to_file()  # Save to file whenever the status is updated
#     def updateEquipment(self, newEquipment):
#         self.equipment = newEquipment
#         self.save_to_file()  # Save to file whenever the status is updated
#     def updateLocation(self, newloc):
#         self.location = newloc
#         self.save_to_file()  # Save to file whenever the status is updated
#     def updateTimeSlot(self, timeSlot):
#         self.timeSlot = timeSlot
#         self.save_to_file()  # Save to file whenever the time slot is updated
#
#     def getAvailability(self, timeRange):
#         from models.room_schedule import RoomSchedule
#         schedules = [s for s in RoomSchedule.all() if s.room == self]
#         for schedule in schedules:
#             schedule_time = DateTimeRange(schedule.startTime, schedule.endTime)
#             if schedule_time.overlaps(timeRange) and schedule.status != "canceled":
#                 return False
#         return True
#
#     def getAverageRating(self):
#         from models.rating import Rating
#         ratings = [r for r in Rating.all() if r.room == self]
#         if not ratings:
#             return 0.0
#         return sum(r.stars for r in ratings) / len(ratings)
#
#     @classmethod
#     def load_from_file(cls):
#         """Load rooms from spaces.json into memory, avoiding duplicates."""
#         try:
#             with open(cls._data_file, 'r') as f:
#                 data = json.load(f)
#                 cls._rooms.clear()  # Clear existing rooms to avoid duplicates
#                 seen_room_ids = set()  # Track roomIDs to detect duplicates in the file
#                 for room_data in data:
#                     roomID = room_data['roomID']
#                     if roomID in seen_room_ids:
#                         print(f"Warning: Duplicate roomID {roomID} found in {cls._data_file}. Skipping this entry.")
#                         continue
#                     seen_room_ids.add(roomID)
#
#                     timeSlot = None
#                     if room_data.get('timeSlot'):
#                         timeSlot = DateTimeRange(
#                             room_data['timeSlot']['startTime'],
#                             room_data['timeSlot']['endTime']
#                         )
#                     cls(
#                         roomID=room_data['roomID'],
#                         type=room_data['type'],
#                         capacity=room_data['capacity'],
#                         equipment=room_data.get('equipment', []),
#                         status=room_data.get('status', 'available'),
#                         location=room_data.get('location', ''),
#                         timeSlot=timeSlot
#                     )
#         except FileNotFoundError:
#             print(f"Warning: {cls._data_file} not found. Starting with empty room list.")
#
#     @classmethod
#     def save_to_file(cls):
#         """Save all rooms to spaces.json."""
#         data = [
#             {
#                 'roomID': room.roomID,
#                 'type': room.type,
#                 'capacity': room.capacity,
#                 'equipment': room.equipment,
#                 'status': room.status,
#                 'location': room.location,
#                 'timeSlot': room.timeSlot.to_dict() if room.timeSlot else None
#             }
#             for room in cls._rooms
#         ]
#         with open(cls._data_file, 'w') as f:
#             json.dump(data, f, indent=4)
#
#     @classmethod
#     def find_by_id(cls, room_id):
#         return next((room for room in cls._rooms if room.roomID == room_id), None)
#
#     @classmethod
#     def all(cls):
#         return cls._rooms
#
#
# # Load rooms from file when the module is imported
# Room.load_from_file()


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


    def getAvailability(self, timeSlot):
        if self.status != "available":
            return False
        if not self.timeSlot:
            return True  # Phòng chưa được đặt gì thì rảnh
        return not self.timeSlot.overlaps(timeSlot)

    def __init__(self, roomID, type, capacity, equipment=None, status="", location=""):
        self.roomID = roomID
        self.type = type
        self.capacity = capacity
        self.equipment = equipment or []
        self.status = status
        self.location = location
        Room._rooms.append(self)

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