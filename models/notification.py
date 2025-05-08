# from datetime import datetime
#
# class Notification:
#     def __init__(self, messageID, recipient, content, sendTime):
#         self.messageID = messageID
#         self.recipient = recipient
#         self.content = content
#         self.sendTime = sendTime
#
#     def send(self):
#         # Simulate sending a notification
#         print(f"Notification sent to {self.recipient.email}: {self.content} at {self.sendTime}")

from sqlalchemy import Column, Integer, String, ForeignKey, DateTime
from sqlalchemy.orm import relationship
from data.database import Base, SessionLocal
from datetime import datetime

class Notification(Base):
    __tablename__ = "notifications"

    messageID = Column(Integer, primary_key=True, index=True)
    recipient_id = Column(Integer, ForeignKey("students.userID"))
    content = Column(String)
    sendTime = Column(DateTime, default=datetime.now)

    recipient = relationship("Student", back_populates="notifications")

    def send(self):
        print(f"Notification sent to {self.recipient.email}: {self.content} at {self.sendTime}")