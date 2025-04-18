from datetime import datetime
import json

class SensorData:
    def __init__(self, temperature, humidity, motionDetected, device):
        self.temperature = temperature
        self.humidity = humidity
        self.motionDetected = motionDetected
        self.timestamp = datetime.now()
        self.device = device

    def isDataValid(self):
        # Example validation: temperature between 0 and 50, humidity between 0 and 100
        return 0 <= self.temperature <= 50 and 0 <= self.humidity <= 100

    def toJSON(self):
        return json.dumps({
            "temperature": self.temperature,
            "humidity": self.humidity,
            "motionDetected": self.motionDetected,
            "timestamp": self.timestamp.strftime('%Y-%m-%d %H:%M:%S')
        })