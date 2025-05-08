# from flask import Flask, redirect, url_for, render_template
# from controllers.auth_controller import auth_bp
# from controllers.reservation_controller import reservation_bp
# from controllers.iot_controller import iot_bp
# from models.user import Student, Admin
# from models.study_space import Room
# from models.iot_device import IoTDevice
# from models.reservation import Booking
# from models.room_schedule import RoomSchedule
# from datetime import datetime, timedelta
#
# app = Flask(__name__, template_folder='views/template', static_folder='views/static')
# app.secret_key = 's3mrs_demo'  # Required for session management
#
# # Register blueprints for controllers
# app.register_blueprint(auth_bp, url_prefix='/auth')
# app.register_blueprint(reservation_bp, url_prefix='/')
# app.register_blueprint(iot_bp, url_prefix='/iot')
#
# # Initialize sample data
# def init_data():
#     # Create sample users
#     Student("1", "Student One", "student1@hcmut.edu.vn")
#     Admin("2", "Admin One", "admin1@hcmut.edu.vn")
#
#     # Create sample rooms with equipment
#     room1 = Room("P.101", "individual", 2, ["Projector", "Air Conditioner"], "reserved", "Building A")
#     room2 = Room("P.102", "group", 6, ["Projector", "Air Conditioner"], "available", "Building B")
#     room3 = Room("P.103", "individual", 2, ["Projector", "Air Conditioner"], "available", "Building A")
#     room4 = Room("P.104", "group", 6, ["Projector", "Air Conditioner"], "available", "Building B")
#
#     # Create sample bookings for testing
#     start_time = datetime.now() + timedelta(hours=1)
#     end_time = start_time + timedelta(hours=1)
#     student = Student.find_by_id("1")
#     booking = Booking("1", student, room1, {"startTime": start_time, "endTime": end_time})
#     booking.confirm()
#     IoTDevice("AC", "P.101", "ok")
#
# # Initialize data on app startup
# init_data()
#
# # Root route to redirect to login
# @app.route('/')
# def index():
#     return redirect(url_for('auth.login'))
#
# if __name__ == '__main__':
#     app.run(host='0.0.0.0', port=5000, debug=True)

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
            student = Student(userID=1, username="student1", name="Student One", email="student1@hcmut.edu.vn", password="123")
            admin = Admin(userID=2, username="admin1", name="Admin One", email="admin1@hcmut.edu.vn", password="admin")
            db.add_all([student, admin])

            room1 = Room(roomID="P.101", type="individual", capacity=2, equipment='["Projector", "Air Conditioner"]', status="reserved", location="Building A")
            room2 = Room(roomID="P.102", type="group", capacity=6, equipment='["Projector", "Air Conditioner"]', status="available", location="Building B")
            room3 = Room(roomID="P.103", type="individual", capacity=2, equipment='["Projector", "Air Conditioner"]', status="available", location="Building A")
            room4 = Room(roomID="P.104", type="group", capacity=6, equipment='["Projector", "Air Conditioner"]', status="available", location="Building B")
            db.add_all([room1, room2, room3, room4])

            start_time = datetime.now() + timedelta(hours=1)
            end_time = start_time + timedelta(hours=1)
            time_slot = DateTimeRange(startTime=start_time, endTime=end_time)
            db.add(time_slot)

            booking = Booking(bookingID=1, student=student, room=room1, timeSlot=time_slot)
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