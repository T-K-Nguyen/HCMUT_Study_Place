# from datetime import datetime
# import json
#
# class SensorData:
#     def __init__(self, temperature, humidity, motionDetected, device):
#         self.temperature = temperature
#         self.humidity = humidity
#         self.motionDetected = motionDetected
#         self.timestamp = datetime.now()
#         self.device = device
#
#     def isDataValid(self):
#         # Example validation: temperature between 0 and 50, humidity between 0 and 100
#         return 0 <= self.temperature <= 50 and 0 <= self.humidity <= 100
#
#     def toJSON(self):
#         return json.dumps({
#             "temperature": self.temperature,
#             "humidity": self.humidity,
#             "motionDetected": self.motionDetected,
#             "timestamp": self.timestamp.strftime('%Y-%m-%d %H:%M:%S')
#         })

from sqlalchemy import Column, Float, Boolean, DateTime, ForeignKey, Integer
from sqlalchemy.orm import relationship
from data.database import Base, SessionLocal
import json
from datetime import datetime

class SensorData(Base):
    __tablename__ = "sensor_data"

    id = Column(Integer, primary_key=True, index=True)
    temperature = Column(Float)
    humidity = Column(Float)
    motionDetected = Column(Boolean)
    timestamp = Column(DateTime, default=datetime.now)
    device_id = Column(Integer, ForeignKey("iot_devices.deviceID"))

    device = relationship("IoTDevice")

    def isDataValid(self):
        return 0 <= self.temperature <= 50 and 0 <= self.humidity <= 100

    def toJSON(self):
        return json.dumps({
            "temperature": self.temperature,
            "humidity": self.humidity,
            "motionDetected": self.motionDetected,
            "timestamp": self.timestamp.strftime('%Y-%m-%d %H:%M:%S')
        })