from models.study_space import DateTimeRange
class Report:
    _reports = []  # In-memory storage

    def __init__(self, reportID, generatedBy, timeRange, data):
        self.reportID = reportID
        self.generatedBy = generatedBy
        self.timeRange = timeRange
        self.data = data
        Report._reports.append(self)

    def generate(self):
        # Simulate generating report data
        from models.reservation import Booking
        bookings = [b for b in Booking.all() if self.timeRange.overlaps(b.timeSlot)]
        self.data = {
            "total_bookings": len(bookings),
            "usage_rate": len(bookings) / 10.0  # Simplified example
        }
        return self.data

    def export(self, format="json"):
        import json, csv
        if format == "json":
            return json.dumps(self.data)
        elif format == "csv":
            # Simplified CSV export
            with open(f"report_{self.reportID}.csv", "w", newline='') as f:
                writer = csv.writer(f)
                writer.writerow(["Metric", "Value"])
                for key, value in self.data.items():
                    writer.writerow([key, value])
            return f"report_{self.reportID}.csv"
        return None

    @staticmethod
    def all():
        return Report._reports