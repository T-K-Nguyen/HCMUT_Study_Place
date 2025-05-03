from flask import Blueprint, render_template, request, redirect, url_for, session
from models.user import User
from models.study_space import Room
from models.reservation import Booking
from models.iot_device import IoTDevice
from datetime import datetime

auth_bp = Blueprint('auth', __name__)


@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        user_id = request.form['username']
        user = User.find_by_id(user_id)
        if user and user.login():
            session['user'] = {'id': user.userID, 'name': user.name, 'role': user.role}
            return redirect(url_for('reservation.dashboard'))
        return render_template('login.html', error="Thông tin không hợp lệ")
    return render_template('login.html')


@auth_bp.route('/logout', methods=['GET', 'POST'])
def logout():
    if request.method == 'POST':
        user_id = session.get('user', {}).get('id')
        user = User.find_by_id(user_id)
        if user:
            user.logout()
        session.pop('user', None)
        return redirect(url_for('auth.login'))
    return render_template('logout.html')

@auth_bp.route('/profile')
def profile():
    return render_template('profile.html', user=session['user'])

@auth_bp.route('/report')
def report():
    if 'user' not in session or session['user']['role'] != 'admin':
        return redirect(url_for('auth.login'))
    rooms = Room.all()
    bookings = Booking.all()
    devices = IoTDevice.all()
    total_rooms = len(rooms)
    total_bookings = len(bookings)
    in_use = len([r for r in rooms if r.status == 'in_use'])
    total_devices = len(devices)
    active_devices = len([d for d in devices if d.status == 'on'])

    # Simulate IoT device report data as per mockup
    device_reports = []
    for device in devices:
        # Simulate equipment list and maintenance date
        equipment = ["Điều hòa", "Máy chiếu", "Đèn", "Cảm biến"]  # Mocked equipment list
        maintenance_date = datetime.strptime("11/12/2023", "%d/%m/%Y")  # Mocked date
        device_reports.append({
            'room': device.room,
            'equipment': equipment,
            'maintenance_date': maintenance_date.strftime("%d/%m/%Y"),
            'needs_maintenance': device.status != 'on'  # Simulate maintenance need
        })

    maintenance_needed = len([d for d in device_reports if d['needs_maintenance']])
    booking_rate = (total_bookings / total_rooms * 100) if total_rooms > 0 else 0
    avg_time = sum((b.timeSlot.endTime - b.timeSlot.startTime).total_seconds() / 3600 for b in bookings if
                   b.status == 'confirmed') / total_bookings if total_bookings > 0 else 0
    most_booked = max((r.roomID for r in rooms), key=lambda x: len([b for b in bookings if b.room.roomID == x]),
                      default='N/A')
    peak_hours = 'N/A'  # Placeholder
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
                           devices=device_reports,  # Updated to use simulated reports
                           bookings=bookings[:5]  # Show recent 5 bookings
                           )
