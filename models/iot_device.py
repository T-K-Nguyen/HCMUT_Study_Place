from sqlalchemy import Column, Integer, String, ForeignKey
from sqlalchemy.orm import relationship
from data.database import Base, SessionLocal
from models.sensor_data import SensorData

class IoTDevice(Base):
    __tablename__ = "iot_devices"

    deviceID = Column(Integer, primary_key=True, index=True)
    room_id = Column(String, ForeignKey("rooms.roomID"))
    status = Column(String, default="off")

    room = relationship("Room")

    def readSensor(self):
        data = SensorData(
            temperature=22.5,
            humidity=45.0,
            motionDetected=True,
            device=self
        )
        db = SessionLocal()
        db.add(data)
        db.commit()
        db.close()
        return data

    def sendAlert(self):
        print(f"Alert: Device {self.deviceID} in room {self.room.roomID} has an issue. Status: {self.status}")

    @classmethod
    def all(cls):
        db = SessionLocal()
        devices = db.query(cls).all()
        db.close()
        return devices