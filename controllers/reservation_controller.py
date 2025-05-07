# from flask import Blueprint, render_template, request, redirect, url_for, session, jsonify
# from models.study_space import Room, DateTimeRange
# from models.user import User, Student
# from models.reservation import Booking
# from datetime import datetime, timedelta
#
# reservation_bp = Blueprint('reservation', __name__)
#
# @reservation_bp.route('/dashboard')
# def dashboard():
#     if 'user' not in session:
#         return redirect(url_for('auth.login'))
#     time_filter = request.args.get('time')
#     capacity = request.args.get('capacity')
#     equipment = request.args.get('equipment')
#     criteria = {}
#     if time_filter:
#         start = time_filter
#         from datetime import datetime, timedelta
#         end = (datetime.strptime(start, '%Y-%m-%d %H:%M') + timedelta(hours=1)).strftime('%Y-%m-%d %H:%M')
#         criteria['timeSlot'] = {'startTime': start, 'endTime': end}
#     if capacity:
#         criteria['capacity'] = int(capacity)
#     if equipment:
#         criteria['equipment'] = [equipment]
#     user = User.find_by_id(session['user']['id'])
#     if isinstance(user, Student):
#         rooms = user.searchRoom(criteria)
#     else:
#         rooms = Room.all()
#     return render_template('dashboard.html', spaces=rooms)
#
# @reservation_bp.route('/reserve/<space_id>', methods=['GET', 'POST'])
# def reserve_space(space_id):
#     if 'user' not in session or 'id' not in session['user']:
#         return redirect(url_for('auth.login'))
#
#     space = Room.find_by_id(space_id)
#     if not space:
#         return render_template('error.html', message="Phòng không tồn tại."), 404
#
#     if request.method == 'POST':
#         if space.status != 'available':
#             return render_template('error.html', message="Phòng đã được đặt trước."), 400
#
#         try:
#             time = request.form['time']
#             room_type = request.form['room_type']
#         except KeyError as e:
#             return render_template('error.html', message=f"Thiếu thông tin: {str(e)}."), 400
#
#         try:
#             start_dt = datetime.strptime(time, '%Y-%m-%dT%H:%M')
#             end_dt = start_dt + timedelta(hours=1)
#         except ValueError as e:
#             return render_template('error.html',
#                                    message="Định dạng thời gian không hợp lệ. Vui lòng sử dụng định dạng YYYY-MM-DDThh:mm."), 400
#
#         time_slot = DateTimeRange(start_dt, end_dt)
#         user = User.find_by_id(session['user']['id'])
#         booking = user.bookRoom(space, time_slot)
#         if booking:
#             space.updateStatus('reserved')
#             space.updateTimeSlot(time_slot)
#             booking.confirm()
#             return redirect(url_for('reservation.success'))
#         return render_template('error.html', message="Đặt phòng thất bại. Vui lòng thử lại."), 400
#
#     return render_template('reservation.html', space=space)
#
#
# @reservation_bp.route('/cancel/<space_id>', methods=['GET', 'POST'])
# def cancel_reservation(space_id):
#     if 'user' not in session:
#         return redirect(url_for('auth.login'))
#     space = Room.find_by_id(space_id)
#     if not space:
#         return jsonify({'error': 'Không tìm thấy phòng.'}), 404
#
#     if request.method == 'GET':
#         user = User.find_by_id(session['user']['id'])
#         if not isinstance(user, Student):
#             return jsonify({'error': 'Chỉ sinh viên có thể hủy đặt phòng.'}), 403
#         booking = next((b for b in user.bookings if b.room.roomID == space_id and b.status == "confirmed"), None)
#         if not booking:
#             return jsonify({'error': 'Không tìm thấy đặt phòng để hủy.'}), 404
#         return render_template('cancel.html', space=space, booking=booking)
#
#     if request.method == 'POST':
#         user = User.find_by_id(session['user']['id'])
#         if not isinstance(user, Student):
#             return jsonify({'error': 'Chỉ sinh viên có thể hủy đặt phòng.'}), 403
#         booking = next((b for b in user.bookings if b.room.roomID == space_id and b.status == "confirmed"), None)
#         if not booking:
#             return jsonify({'error': 'Không tìm thấy đặt phòng để hủy.'}), 404
#         if booking.status != 'confirmed':
#             return jsonify({'error': 'Đặt phòng này không thể hủy.'}), 400
#         user.cancelBooking(booking.bookingID)
#         space.status = 'available'
#         space.timeSlot = None
#         return jsonify({'message': 'Hủy đặt phòng thành công!'}), 200
#
# @reservation_bp.route('/checkin/<space_id>', methods=['GET', 'POST'])
# def checkin(space_id):
#     if 'user' not in session:
#         return redirect(url_for('auth.login'))
#     space = Room.find_by_id(space_id)
#     if not space or space.status != 'reserved':
#         return render_template('error.html', message="Không thể check-in. Phòng không tồn tại hoặc chưa được đặt."), 404
#
#     user = User.find_by_id(session['user']['id'])
#     if not isinstance(user, Student):
#         return render_template('error.html', message="Chỉ sinh viên có thể check-in."), 403
#
#     # Find the booking for this space
#     booking = next((b for b in user.bookings if b.room.roomID == space_id and b.status == "confirmed"), None)
#     if not booking:
#         return render_template('error.html', message="Không tìm thấy đặt phòng để check-in."), 404
#
#     if booking.student.userID != user.userID:
#         return render_template('error.html', message="Bạn không có quyền check-in cho đặt phòng này."), 403
#
#     if request.method == 'POST':
#         if request.is_json:
#             data = request.get_json()
#             qr_code = data.get('qr_code')
#         else:
#             qr_code = request.form.get('qr_code')
#
#         if not qr_code:
#             return jsonify({'error': 'Mã QR không được cung cấp.'}), 400
#
#         if qr_code == booking.qrCode:
#             if user.checkIn(qr_code):
#                 space.status = 'available'
#                 space.timeSlot = None
#                 booking.status = "completed"
#                 return jsonify({'message': 'Check-in thành công!', 'redirect': url_for('reservation.dashboard')}), 200
#             return jsonify({'error': 'Check-in thất bại. Vui lòng thử lại.'}), 400
#         return jsonify({'error': 'Mã QR không hợp lệ.'}), 400
#
#     return render_template('checkin.html', space=space, booking=booking, message=None, error=None)
# @reservation_bp.route('/success')
# def success():
#     return render_template('success.html', message="Reservation successful. QR code sent to email.")
#
#
# @reservation_bp.route('/auto_cancel')
# def auto_cancel():
#     if 'user' not in session or session['user']['role'] != 'admin':
#         return redirect(url_for('auth.login'))
#     from datetime import datetime
#     for booking in Booking.all():
#         if booking.timeSlot.startTime < datetime.now() and booking.status == "pending":
#             booking.cancel()
#             print(f"Auto-canceled booking {booking.bookingID}")
#     return redirect(url_for('reservation.dashboard'))

from flask import Blueprint, render_template, request, redirect, url_for, session, jsonify
from models.study_space import Room, DateTimeRange
from models.user import User, Student
from models.reservation import Booking
from data.database import get_db
from datetime import datetime, timedelta
from sqlalchemy.orm import joinedload

reservation_bp = Blueprint('reservation', __name__)


@reservation_bp.route('/dashboard')
def dashboard():
    if 'user' not in session:
        return redirect(url_for('auth.login'))

    db = next(get_db())
    time_filter = request.args.get('time')
    capacity = request.args.get('capacity')
    equipment = request.args.get('equipment')
    criteria = {}
    if time_filter:
        start = datetime.strptime(time_filter, '%Y-%m-%dT%H:%M')
        end = start + timedelta(hours=1)
        criteria['timeSlot'] = DateTimeRange(start, end)
    if capacity:
        criteria['capacity'] = int(capacity)
    if equipment:
        criteria['equipment'] = [equipment]

    user = db.query(User).filter_by(userID=session['user']['id']).first()
    if not user:
        db.close()
        return redirect(url_for('auth.login'))

    rooms = db.query(Room).options(joinedload(Room.timeSlot)).all()

    # Convert rooms to a format suitable for the template
    import json
    spaces = [
        {
            'id': room.roomID,
            'capacity': room.capacity,
            'status': room.status,
            'equipment': json.loads(room.equipment) if isinstance(room.equipment, str) else room.equipment,
            'timeslot': room.timeSlot.to_string() if room.timeSlot else "available"
        } for room in rooms
    ]

    db.close()
    return render_template('dashboard.html', spaces=spaces)


@reservation_bp.route('/reserve/<space_id>', methods=['GET', 'POST'])
def reserve_space(space_id):
    if 'user' not in session or 'id' not in session['user']:
        return redirect(url_for('auth.login'))

    db = next(get_db())

    space = db.query(Room).options(joinedload(Room.timeSlot)).filter_by(roomID=space_id).first()
    # space = db.query(Room).filter_by(roomID=space_id).first()
    if not space:
        db.close()
        return render_template('error.html', message="Phòng không tồn tại."), 404

    if request.method == 'POST':
        if space.status != 'available':
            db.close()
            return render_template('error.html', message="Phòng đã được đặt trước."), 400

        try:
            time = request.form['time']
            room_type = request.form['room_type']
        except KeyError as e:
            db.close()
            return render_template('error.html', message=f"Thiếu thông tin: {str(e)}."), 400

        try:
            start_dt = datetime.strptime(time, '%Y-%m-%dT%H:%M')
            end_dt = start_dt + timedelta(hours=1)
        except ValueError as e:
            db.close()
            return render_template('error.html',
                                   message="Định dạng thời gian không hợp lệ. Vui lòng sử dụng định dạng YYYY-MM-DDThh:mm."), 400

        time_slot = DateTimeRange(startTime=start_dt, endTime=end_dt)
        db.add(time_slot)  # Save the time slot to the database
        db.commit()

        user = db.query(Student).filter_by(userID=session['user']['id']).first()
        if not user:
            db.close()
            return render_template('error.html', message="Chỉ sinh viên có thể đặt phòng."), 403

        booking = user.bookRoom(db, space, time_slot)
        print("\nBooking:", booking)
        print("\nSpace:", space)
        print("\ntimeslot:", time_slot.to_string())
        if booking:
            space.updateStatus('reserved')
            space.updateTimeSlot(time_slot)
            #booking.confirm()
            db.commit()
            db.close()
            return redirect(url_for('reservation.success'))
        db.close()
        return render_template('error.html', message="Đặt phòng thất bại. Vui lòng thử lại."), 400

    db.close()
    return render_template('reservation.html', space=space)


@reservation_bp.route('/cancel/<space_id>', methods=['GET', 'POST'])
def cancel_reservation(space_id):
    if 'user' not in session:
        return redirect(url_for('auth.login'))

    db = next(get_db())
    space = db.query(Room).filter_by(roomID=space_id).first()
    if not space:
        db.close()
        return jsonify({'error': 'Không tìm thấy phòng.'}), 404

    user = db.query(Student).filter_by(userID=session['user']['id']).first()
    if not user:
        db.close()
        return jsonify({'error': 'Chỉ sinh viên có thể hủy đặt phòng.'}), 403

    booking = db.query(Booking).filter_by(room_id=space_id, student_id=user.userID, status="confirmed").first()
    if not booking:
        db.close()
        return jsonify({'error': 'Không tìm thấy đặt phòng để hủy.'}), 404

    if request.method == 'GET':
        db.close()
        return render_template('cancel.html', space=space, booking=booking)

    if request.method == 'POST':
        if booking.status != 'confirmed':
            db.close()
            return jsonify({'error': 'Đặt phòng này không thể hủy.'}), 400
        user.cancelBooking(booking.bookingID)
        space.updateStatus('available')
        space.updateTimeSlot(None)
        db.commit()
        db.close()
        return jsonify({'message': 'Hủy đặt phòng thành công!'}), 200


@reservation_bp.route('/checkin/<space_id>', methods=['GET', 'POST'])
def checkin(space_id):
    if 'user' not in session:
        return redirect(url_for('auth.login'))

    db = next(get_db())
    space = db.query(Room).options(joinedload(Room.timeSlot)).filter_by(roomID=space_id).first()
    if not space or space.status != 'reserved':
        db.close()
        return render_template('error.html', message="Không thể check-in. Phòng không tồn tại hoặc chưa được đặt."), 404

    user = db.query(Student).filter_by(userID=session['user']['id']).first()
    if not user:
        db.close()
        return render_template('error.html', message="Chỉ sinh viên có thể check-in."), 403

    booking = db.query(Booking).filter_by(room_id=space_id, student_id=user.userID, status="confirmed").first()
    print(f"Checking booking for room_id={space_id}, student_id={user.userID}, status=confirmed")
    if booking:
        print("Booking found:", booking.bookingID, booking.status)
        print("Status:", booking.status)
        print("QR:", booking.qrCode)
    else:
        print("No booking found.")
        # Debug: Check all bookings for this room and user
        all_bookings = db.query(Booking).filter_by(room_id=space_id, student_id=user.userID).all()
        for b in all_bookings:
            print(f"Existing booking: bookingID={b.bookingID}, status={b.status}, qrCode={b.qrCode}")

    if not booking:
        db.close()
        return render_template('error.html', message="Không tìm thấy đặt phòng để check-in."), 404

    if booking.student.userID != user.userID:
        db.close()
        return render_template('error.html', message="Bạn không có quyền check-in cho đặt phòng này."), 403

    if request.method == 'POST':
        if request.is_json:
            data = request.get_json()
            qr_code = data.get('qr_code')
        else:
            qr_code = request.form.get('qr_code')

        if not qr_code:
            db.close()
            return jsonify({'error': 'Mã QR không được cung cấp.'}), 400

        if qr_code == booking.qrCode:
            if user.checkIn(qr_code):
                space.updateStatus('available')
                space.updateTimeSlot(None)
                booking.status = "completed"
                db.commit()
                db.close()
                return jsonify({'message': 'Check-in thành công!', 'redirect': url_for('reservation.dashboard')}), 200
            db.close()
            return jsonify({'error': 'Check-in thất bại. Vui lòng thử lại.'}), 400
        db.close()
        return jsonify({'error': 'Mã QR không hợp lệ.'}), 400

    db.close()
    return render_template('checkin.html', space=space, booking=booking, message=None, error=None)


@reservation_bp.route('/success')
def success():
    return render_template('success.html', message="Reservation successful. QR code sent to email.")


@reservation_bp.route('/auto_cancel')
def auto_cancel():
    if 'user' not in session or session['user']['role'] != 'admin':
        return redirect(url_for('auth.login'))

    db = next(get_db())
    bookings = db.query(Booking).filter_by(status="pending").all()
    for booking in bookings:
        if booking.timeSlot.startTime < datetime.now():
            booking.cancel()
            print(f"Auto-canceled booking {booking.bookingID}")
            db.commit()
    db.close()
    return redirect(url_for('reservation.dashboard'))