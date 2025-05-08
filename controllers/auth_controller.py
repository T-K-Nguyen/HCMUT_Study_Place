# from flask import Blueprint, render_template, request, redirect, url_for, session
# from models.user import User
# from models.study_space import Room
# from models.reservation import Booking
# from models.iot_device import IoTDevice
# from datetime import datetime
#
# auth_bp = Blueprint('auth', __name__)
#
# @auth_bp.route('/')
# def home():
#     if 'user' not in session:  # Check if user is not logged in
#         return redirect(url_for('auth.login'))  # Redirect to login page
#     return render_template('home.html', now=datetime.now())
#
# @auth_bp.route('/login', methods=['GET', 'POST'])
# def login():
#     if request.method == 'POST':
#         user_id = request.form['username']
#         user = User.find_by_id(user_id)
#         if user and user.login():
#             session['user'] = {'id': user.userID, 'name': user.name, 'role': user.role}
#             return redirect(url_for('auth.home'))
#         return render_template('login.html', error="Thông tin không hợp lệ")
#     return render_template('login.html')
#
#
# @auth_bp.route('/logout', methods=['GET', 'POST'])
# def logout():
#     if request.method == 'POST':
#         user_id = session.get('user', {}).get('id')
#         user = User.find_by_id(user_id)
#         if user:
#             user.logout()
#         session.pop('user', None)
#         return redirect(url_for('auth.login'))
#     return render_template('logout.html')
#
# @auth_bp.route('/profile')
# def profile():
#     return render_template('profile.html', user=session['user'])
#
# @auth_bp.route('/report')
# def report():
#     if 'user' not in session or session['user']['role'] != 'admin':
#         return redirect(url_for('auth.login'))
#     rooms = Room.all()
#     bookings = Booking.all()
#     devices = IoTDevice.all()
#     total_rooms = len(rooms)
#     total_bookings = len(bookings)
#     in_use = len([r for r in rooms if r.status == 'in_use'])
#     total_devices = len(devices)
#     active_devices = len([d for d in devices if d.status == 'on'])
#
#     # Simulate IoT device report data as per mockup
#     device_reports = []
#     for device in devices:
#         # Simulate equipment list and maintenance date
#         equipment = ["Điều hòa", "Máy chiếu", "Đèn", "Cảm biến"]  # Mocked equipment list
#         maintenance_date = datetime.strptime("11/12/2023", "%d/%m/%Y")  # Mocked date
#         device_reports.append({
#             'room': device.room,
#             'equipment': equipment,
#             'maintenance_date': maintenance_date.strftime("%d/%m/%Y"),
#             'needs_maintenance': device.status != 'on'  # Simulate maintenance need
#         })
#
#     maintenance_needed = len([d for d in device_reports if d['needs_maintenance']])
#     booking_rate = (total_bookings / total_rooms * 100) if total_rooms > 0 else 0
#     avg_time = sum((b.timeSlot.endTime - b.timeSlot.startTime).total_seconds() / 3600 for b in bookings if
#                    b.status == 'confirmed') / total_bookings if total_bookings > 0 else 0
#     most_booked = max((r.roomID for r in rooms), key=lambda x: len([b for b in bookings if b.room.roomID == x]),
#                       default='N/A')
#     peak_hours = 'N/A'  # Placeholder
#     return render_template('report.html',
#                            total_rooms=total_rooms,
#                            active_devices=active_devices,
#                            total_devices=total_devices,
#                            booking_rate=round(booking_rate, 2),
#                            in_use=in_use,
#                            total_bookings=total_bookings,
#                            avg_time=round(avg_time, 2),
#                            most_booked_room=most_booked,
#                            peak_hours=peak_hours,
#                            devices=device_reports,  # Updated to use simulated reports
#                            bookings=bookings[:5]  # Show recent 5 bookings
#                            )

from flask import Blueprint, render_template, request, redirect, url_for, session
from models.user import User, Student, Admin
from models.study_space import Room
from models.reservation import Booking
from models.iot_device import IoTDevice
from data.database import get_db
from datetime import datetime
import logging

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

auth_bp = Blueprint('auth', __name__)


@auth_bp.route('/')
def home():
    if 'user' not in session:
        return redirect(url_for('auth.login'))
    db = next(get_db())
    current_time = datetime.now()
    db.close()
    return render_template('home.html', now=current_time)


@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        db = next(get_db())
        user = db.query(User).filter_by(username=username).first()
        db.close()

        if user and user.check_password(password):
            session['user'] = {'id': user.userID, 'name': user.name, 'role': user.role}
            return redirect(url_for('auth.home'))
        else:
            session.pop('user', None)  # Ensure session is cleared on failure
            error_msg = "Invalid username or password"
            return render_template('login.html', error=error_msg)

    return render_template('login.html')


@auth_bp.route('/logout', methods=['GET', 'POST'])
def logout():
    if request.method == 'POST':
        user_id = session.get('user', {}).get('id')
        db = next(get_db())
        user = db.query(User).filter_by(userID=user_id).first()
        if user:
            user.logout()
            db.commit()
        session.pop('user', None)
        db.close()
        return redirect(url_for('auth.login'))
    return render_template('logout.html')


@auth_bp.route('/profile')
def profile():
    db = next(get_db())
    user = db.query(User).filter_by(userID=session['user']['id']).first()
    db.close()
    return render_template('profile.html', user=session['user'] if user else None)


@auth_bp.route('/report')
def report():
    if 'user' not in session or session['user']['role'] != 'admin':
        return redirect(url_for('auth.login'))

    db = next(get_db())
    rooms = db.query(Room).all()
    bookings = db.query(Booking).all()
    devices = db.query(IoTDevice).all()
    db.close()

    total_rooms = len(rooms)
    total_bookings = len(bookings)
    in_use = len([r for r in rooms if r.status == 'in_use'])
    total_devices = len(devices)
    active_devices = len([d for d in devices if d.status == 'on'])

    device_reports = []
    for device in devices:
        equipment = ["Điều hòa", "Máy chiếu", "Đèn", "Cảm biến"]
        maintenance_date = datetime.strptime("11/12/2023", "%d/%m/%Y")
        device_reports.append({
            'room': device.room,
            'equipment': equipment,
            'maintenance_date': maintenance_date.strftime("%d/%m/%Y"),
            'needs_maintenance': device.status != 'on'
        })

    maintenance_needed = len([d for d in device_reports if d['needs_maintenance']])
    booking_rate = (total_bookings / total_rooms * 100) if total_rooms > 0 else 0
    avg_time = sum((b.timeSlot.endTime - b.timeSlot.startTime).total_seconds() / 3600 for b in bookings if
                   b.status == 'confirmed') / total_bookings if total_bookings > 0 else 0
    most_booked = max((r.roomID for r in rooms), key=lambda x: len([b for b in bookings if b.room.roomID == x]),
                      default='N/A')
    peak_hours = 'N/A'

    return render_template('report.html',
                           total_rooms=total_rooms,
                           active_devices=active_devices,
                           total_devices=total_devices,
                           booking_rate=round(booking_rate, 2),
                           in_use=in_use,
                           total_bookings=total_bookings,
                           avg_time=round(avg_time, 2),
                           most_booked_room=most_booked,
                           peak_hours=peak_hours,
                           devices=device_reports,
                           bookings=bookings[:5])