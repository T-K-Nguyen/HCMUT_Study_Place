from flask import Blueprint, render_template, request, redirect, url_for, session, jsonify
from models.study_space import Room
from models.user import User, Student
from models.reservation import Booking

reservation_bp = Blueprint('reservation', __name__)

@reservation_bp.route('/dashboard')
def dashboard():
    if 'user' not in session:
        return redirect(url_for('auth.login'))
    time_filter = request.args.get('time')
    capacity = request.args.get('capacity')
    equipment = request.args.get('equipment')
    criteria = {}
    if time_filter:
        start = time_filter
        from datetime import datetime, timedelta
        end = (datetime.strptime(start, '%Y-%m-%d %H:%M') + timedelta(hours=1)).strftime('%Y-%m-%d %H:%M')
        criteria['timeSlot'] = {'startTime': start, 'endTime': end}
    if capacity:
        criteria['capacity'] = int(capacity)
    if equipment:
        criteria['equipment'] = [equipment]
    user = User.find_by_id(session['user']['id'])
    if isinstance(user, Student):
        rooms = user.searchRoom(criteria)
    else:
        rooms = Room.all()
    return render_template('dashboard.html', spaces=rooms)

@reservation_bp.route('/reserve/<space_id>', methods=['GET', 'POST'])
def reserve_space(space_id):
    if 'user' not in session:
        return redirect(url_for('auth.login'))
    space = Room.find_by_id(space_id)
    if not space:
        return "Space not available", 404
    if request.method == 'POST':
        if space.status != 'available':
            return "Space not available", 404
        start_time = request.form['start_time']
        room_type = request.form['room_type']
        end_time = request.form.get('end_time', None)
        if not end_time:
            from datetime import datetime, timedelta
            end_time = (datetime.strptime(start_time, '%Y-%m-%d %H:%M') + timedelta(hours=1)).strftime('%Y-%m-%d %H:%M')
        time_slot = {'startTime': start_time, 'endTime': end_time}
        user = User.find_by_id(session['user']['id'])
        if isinstance(user, Student):
            booking = user.bookRoom(space, time_slot)
            if booking:
                space.status = 'reserved'
                space.timeSlot = time_slot
                return redirect(url_for('reservation.success'))
        return "Booking failed", 400
    return render_template('reservation.html', space=space)

@reservation_bp.route('/cancel/<space_id>', methods=['GET', 'POST'])
def cancel_reservation(space_id):
    if 'user' not in session:
        return redirect(url_for('auth.login'))
    space = Room.find_by_id(space_id)
    if not space:
        return jsonify({'error': 'Không tìm thấy phòng.'}), 404

    if request.method == 'GET':
        user = User.find_by_id(session['user']['id'])
        if not isinstance(user, Student):
            return jsonify({'error': 'Chỉ sinh viên có thể hủy đặt phòng.'}), 403
        booking = next((b for b in user.bookings if b.room.roomID == space_id and b.status == "confirmed"), None)
        if not booking:
            return jsonify({'error': 'Không tìm thấy đặt phòng để hủy.'}), 404
        return render_template('cancel.html', space=space, booking=booking)

    if request.method == 'POST':
        user = User.find_by_id(session['user']['id'])
        if not isinstance(user, Student):
            return jsonify({'error': 'Chỉ sinh viên có thể hủy đặt phòng.'}), 403
        booking = next((b for b in user.bookings if b.room.roomID == space_id and b.status == "confirmed"), None)
        if not booking:
            return jsonify({'error': 'Không tìm thấy đặt phòng để hủy.'}), 404
        if booking.status != 'confirmed':
            return jsonify({'error': 'Đặt phòng này không thể hủy.'}), 400
        user.cancelBooking(booking.bookingID)
        space.status = 'available'
        space.timeSlot = None
        return jsonify({'message': 'Hủy đặt phòng thành công!'}), 200

@reservation_bp.route('/checkin/<space_id>', methods=['GET', 'POST'])
def checkin(space_id):
    if 'user' not in session:
        return redirect(url_for('auth.login'))
    space = Room.find_by_id(space_id)
    if not space or space.status != 'reserved':
        return "Cannot check-in", 404
    user = User.find_by_id(session['user']['id'])
    if not isinstance(user, Student):
        return "Only students can check in", 403
    if request.method == 'POST':
        qr_code = request.form['qr_code']
        if user.checkIn(qr_code):
            return render_template('checkin.html', space=space, message="Check-in successful")
        return render_template('checkin.html', space=space, error="Invalid QR code")
    return render_template('checkin.html', space=space)

@reservation_bp.route('/success')
def success():
    return render_template('success.html', message="Reservation successful. QR code sent to email.")

@reservation_bp.route('/auto_cancel')
def auto_cancel():
    if 'user' not in session or session['user']['role'] != 'admin':
        return redirect(url_for('auth.login'))
    from datetime import datetime
    for booking in Booking.all():
        if booking.timeSlot.startTime < datetime.now() and booking.status == "pending":
            booking.cancel()
            print(f"Auto-canceled booking {booking.bookingID}")
    return redirect(url_for('reservation.dashboard'))