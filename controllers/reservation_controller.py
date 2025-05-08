from flask import Blueprint, render_template, request, redirect, url_for, session, jsonify
from models.study_space import Room, DateTimeRange
from models.user import User, Student
from models.reservation import Booking
from data.database import get_db
from datetime import datetime, timedelta
from sqlalchemy.orm import joinedload
import json
reservation_bp = Blueprint('reservation', __name__)


@reservation_bp.route('/dashboard')
def dashboard():
    if 'user' not in session:
        return redirect(url_for('auth.login'))


    db = next(get_db())

    time_filter = request.args.get('time')
    capacity = request.args.get('capacity')
    equipment = request.args.get('equipment[]')  # Adjusted to match multiple selection
    page = int(request.args.get('page', 1))  # Get page number, default to 1
    
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
    db.close()

    #pages for multiple room
    ITEMS_PER_PAGE = 12
    start = (page - 1) * ITEMS_PER_PAGE
    end = start + ITEMS_PER_PAGE
    paginated_rooms = rooms[start:end]
    total_rooms = len(rooms)
    spaces = [
        {
            'id': room.roomID,
            'capacity': room.capacity,
            'status': room.status,
            'equipment': json.loads(room.equipment) if isinstance(room.equipment, str) else room.equipment,
            'timeslot': room.timeSlot.to_string() if room.timeSlot else "available"
        } for room in paginated_rooms
    ]
    return render_template('dashboard.html', 
                           spaces=spaces,
                           current_page=page, 
                           total_spaces=total_rooms)

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
    print(f"\nChecking booking for room_id={space_id}, student_id={user.userID}, status=confirmed")
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

# @reservation_bp.route('/success')
# def success():
#
#     return render_template('success.html', message="Checkin successful. Rememember to return on time.")


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