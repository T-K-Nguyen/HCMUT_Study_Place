from flask import Flask, redirect, url_for, render_template
from controllers.auth_controller import auth_bp
from controllers.reservation_controller import reservation_bp
from controllers.iot_controller import iot_bp
from models.user import Student, Admin
from models.study_space import Room
from models.iot_device import IoTDevice
from models.reservation import Booking
from models.room_schedule import RoomSchedule
from datetime import datetime, timedelta

app = Flask(__name__, template_folder='views/template', static_folder='views/static')
app.secret_key = 's3mrs_demo'  # Required for session management

# Register blueprints for controllers
app.register_blueprint(auth_bp, url_prefix='/auth')
app.register_blueprint(reservation_bp, url_prefix='/')
app.register_blueprint(iot_bp, url_prefix='/iot')

# Initialize sample data
def init_data():
    # Create sample users
    Student("1", "Student One", "student1@hcmut.edu.vn")
    Admin("2", "Admin One", "admin1@hcmut.edu.vn")

    # Create sample rooms with equipment
    room1 = Room("P.101", "individual", 2, ["Projector", "Air Conditioner"], "reserved", "Building A")
    room2 = Room("P.102", "group", 6, ["Projector", "Air Conditioner"], "available", "Building B")
    room3 = Room("P.103", "individual", 2, ["Projector", "Air Conditioner"], "available", "Building A")
    room4 = Room("P.104", "group", 6, ["Projector", "Air Conditioner"], "available", "Building B")

    # Create sample bookings for testing
    start_time = datetime.now() + timedelta(hours=1)
    end_time = start_time + timedelta(hours=1)
    student = Student.find_by_id("1")
    booking = Booking("1", student, room1, {"startTime": start_time, "endTime": end_time})
    booking.confirm()
    IoTDevice("AC", "P.101", "ok")

# Initialize data on app startup
init_data()

# Root route to redirect to login
@app.route('/')
def index():
    return redirect(url_for('auth.login'))

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)