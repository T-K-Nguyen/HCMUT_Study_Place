class IoTDevice:
    _devices = []  # In-memory storage

    def __init__(self, deviceID, room, status="off"):
        self.deviceID = deviceID
        self.room = room
        self.status = status
        IoTDevice._devices.append(self)

    def readSensor(self):
        from models.sensor_data import SensorData
        # Simulate sensor reading
        data = SensorData(
            temperature=22.5,
            humidity=45.0,
            motionDetected=True,
            device=self
        )
        return data

    def sendAlert(self):
        # Simulate sending an alert (e.g., to technician)
        print(f"Alert: Device {self.deviceID} in room {self.room.roomID} has an issue. Status: {self.status}")

    @staticmethod
    def all():
        return IoTDevice._devices