from datetime import datetime

class Rating:
    _ratings = []  # In-memory storage

    def __init__(self, ratingID, student, room, stars, comment):
        self.ratingID = ratingID
        self.student = student
        self.room = room
        self.stars = stars
        self.comment = comment
        self.timestamp = datetime.now()
        Rating._ratings.append(self)

    def save(self):
        if self not in Rating._ratings:
            Rating._ratings.append(self)

    @staticmethod
    def all():
        return Rating._ratings
