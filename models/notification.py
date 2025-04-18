from datetime import datetime

class Notification:
    def __init__(self, messageID, recipient, content, sendTime):
        self.messageID = messageID
        self.recipient = recipient
        self.content = content
        self.sendTime = sendTime

    def send(self):
        # Simulate sending a notification
        print(f"Notification sent to {self.recipient.email}: {self.content} at {self.sendTime}")
