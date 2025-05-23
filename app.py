from flask import Flask, redirect, url_for
from controllers.auth_controller import auth_bp
from controllers.reservation_controller import reservation_bp
from controllers.iot_controller import iot_bp
from data.database import Base, engine, get_db
from models.user import User, Student, Admin
from models.study_space import Room, DateTimeRange
from models.iot_device import IoTDevice
from models.reservation import Booking
from models.room_schedule import RoomSchedule
from datetime import datetime, timedelta
import json
import uuid

app = Flask(__name__, template_folder='views/template', static_folder='views/static')
app.secret_key = 's3mrs_demo'

app.register_blueprint(auth_bp, url_prefix='/auth')
app.register_blueprint(reservation_bp, url_prefix='/')
app.register_blueprint(iot_bp, url_prefix='/iot')

def init_db():
    Base.metadata.create_all(bind=engine)
    print("Database tables created.")

def populate_initial_data():
    db = next(get_db())
    try:
        if not db.query(User).first():
            student1 = Student(userID=1, username="student1", name="Student One", email="student1@hcmut.edu.vn", password="123")
            student2 = Student(userID=2, username="student2", name="Student Two", email="student2@hcmut.edu.vn", password="123")
            student3 = Student(userID=4, username="student4", name="Student four", email="student5@hcmut.edu.vn",
                               password="123")
            student4 = Student(userID=5, username="student5", name="Student five", email="student6@hcmut.edu.vn",
                               password="123")
            admin = Admin(userID=3, username="admin1", name="Admin One", email="admin1@hcmut.edu.vn", password="admin")
            db.add_all([student1, student2, student3, student4, admin])

            # Danh sách các phòng mẫu
            room1 = Room(roomID="P.100", type="individual", capacity=2, equipment='["Projector", "Air Conditioner"]',
                         status="reserved", location="Building A")

            #load existing file
            with open("data/spaces.json", "r") as f:
                room_data = json.load(f)

            for data in room_data:
                # Kiểm tra xem phòng đã tồn tại chưa
                existing_room = db.query(Room).filter_by(roomID=data["roomID"]).first()
                if existing_room:
                    print(f"Room {data['roomID']} already exists. Skipping...")
                    continue

                equipment_json = json.dumps(data["equipment"])
                room = Room(
                    roomID=data["roomID"],
                    type=data["type"],
                    capacity=data["capacity"],
                    equipment=equipment_json,
                    status=data["status"],
                    location=data["location"]
                )
                db.add(room)

            start_time = datetime.now() + timedelta(hours=1)
            end_time = start_time + timedelta(hours=1)
            time_slot = DateTimeRange(startTime=start_time, endTime=end_time)
            db.add(time_slot)

            booking = Booking(student=student1, room=room1, timeSlot=time_slot)
            booking.qrCode = str(uuid.uuid4())  # Generate a unique QR code
            booking.status = "confirmed"  # Explicitly set to confirmed
            booking.confirm()  # Should set room status to "reserved"
            db.add(booking)

            iot_device = IoTDevice(deviceID=1, room_id="P.101", status="ok")
            db.add(iot_device)

            db.commit()
            print("Initial data populated.")
            print(f"Generated QR Code for booking: {booking.qrCode}")
        else:
            print("Database already contains data. Skipping population.")
    except Exception as e:
        db.rollback()
        print(f"Error populating initial data: {e}")
    finally:
        db.close()

with app.app_context():
    init_db()
    populate_initial_data()


@app.route('/')
def index():
    return redirect(url_for('auth.login'))

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)