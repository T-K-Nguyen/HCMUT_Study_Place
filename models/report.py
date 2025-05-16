# from models.study_space import DateTimeRange
# class Report:
#     _reports = []  # In-memory storage
#
#     def __init__(self, reportID, generatedBy, timeRange, data):
#         self.reportID = reportID
#         self.generatedBy = generatedBy
#         self.timeRange = timeRange
#         self.data = data
#         Report._reports.append(self)
#
#     def generate(self):
#         # Simulate generating report data
#         from models.reservation import Booking
#         bookings = [b for b in Booking.all() if self.timeRange.overlaps(b.timeSlot)]
#         self.data = {
#             "total_bookings": len(bookings),
#             "usage_rate": len(bookings) / 10.0  # Simplified example
#         }
#         return self.data
#
#     def export(self, format="json"):
#         import json, csv
#         if format == "json":
#             return json.dumps(self.data)
#         elif format == "csv":
#             # Simplified CSV export
#             with open(f"report_{self.reportID}.csv", "w", newline='') as f:
#                 writer = csv.writer(f)
#                 writer.writerow(["Metric", "Value"])
#                 for key, value in self.data.items():
#                     writer.writerow([key, value])
#             return f"report_{self.reportID}.csv"
#         return None
#
#     @staticmethod
#     def all():
#         return Report._reports

from sqlalchemy import Column, Integer, String, ForeignKey, DateTime
from sqlalchemy.orm import relationship
from data.database import Base, SessionLocal
import json
import csv

class Report(Base):
    __tablename__ = "reports"

    reportID = Column(Integer, primary_key=True, index=True)
    generatedBy_id = Column(Integer, ForeignKey("users.userID"))
    timeRange_id = Column(Integer, ForeignKey("datetime_ranges.id"))
    data = Column(String)  # Store as JSON string

    generatedBy = relationship("User")
    timeRange = relationship("DateTimeRange")

    def generate(self):
        from models.reservation import Booking
        db = SessionLocal()
        time_range = DateTimeRange(self.timeRange.startTime, self.timeRange.endTime)
        bookings = db.query(Booking).filter(
            Booking.timeSlot.has(DateTimeRange.startTime < self.timeRange.endTime),
            Booking.timeSlot.has(DateTimeRange.endTime > self.timeRange.startTime)
        ).all()
        self.data = json.dumps({
            "total_bookings": len(bookings),
            "usage_rate": len(bookings) / 10.0  # Simplified example
        })
        db.commit()
        db.close()
        return json.loads(self.data)

    def export(self, format="json"):
        data = json.loads(self.data)
        if format == "json":
            return self.data
        elif format == "csv":
            filename = f"report_{self.reportID}.csv"
            with open(filename, "w", newline='') as f:
                writer = csv.writer(f)
                writer.writerow(["Metric", "Value"])
                for key, value in data.items():
                    writer.writerow([key, value])
            return filename
        return None

    @classmethod
    def all(cls):
        db = SessionLocal()
        reports = db.query(cls).all()
        db.close()
        return reports