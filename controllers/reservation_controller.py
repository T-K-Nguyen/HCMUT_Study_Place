from flask import Blueprint, render_template, request, redirect, url_for, session, jsonify
from models.study_space import Room, DateTimeRange
from models.user import User, Student
from models.reservation import Booking
from datetime import datetime, timedelta

reservation_bp = Blueprint('reservation', __name__)

@reservation_bp.route('/dashboard')
def dashboard():
    if 'user' not in session:
        return redirect(url_for('auth.login'))
    
    time_filter = request.args.get('time')
    capacity = request.args.get('capacity')
    equipment = request.args.get('equipment[]')  # Adjusted to match multiple selection
    page = int(request.args.get('page', 1))  # Get page number, default to 1
    
    criteria = {}
    if time_filter:
        start = time_filter
        from datetime import datetime, timedelta
        end = (datetime.strptime(start, '%Y-%m-%dT%H:%M') + timedelta(hours=1)).strftime('%Y-%m-%dT%H:%M')
        criteria['timeSlot'] = {'startTime': start, 'endTime': end}
    if capacity:
        criteria['capacity'] = int(capacity)
    if equipment:
        criteria['equipment'] = request.args.getlist('equipment[]')  # Handle multiple equipment selections

    user = User.find_by_id(session['user']['id'])
    if isinstance(user, Student):
        rooms = user.searchRoom(criteria)
    else:
        rooms = Room.all()

    ITEMS_PER_PAGE = 12
    start = (page - 1) * ITEMS_PER_PAGE
    end = start + ITEMS_PER_PAGE
    paginated_rooms = rooms[start:end]
    total_rooms = len(rooms)

    return render_template('dashboard.html', 
                           spaces=paginated_rooms, 
                           current_page=page, 
                           total_spaces=total_rooms)

@reservation_bp.route('/reserve/<space_id>', methods=['GET', 'POST'])
def reserve_space(space_id):
    if 'user' not in session or 'id' not in session['user']:
        return redirect(url_for('auth.login'))

    space = Room.find_by_id(space_id)
    if not space:
        return render_template('error.html', message="Phòng không tồn tại."), 404

    if request.method == 'POST':
        if space.status != 'available':
            return render_template('error.html', message="Phòng đã được đặt trước."), 400

        try:
            time = request.form['time']
            room_type = request.form['room_type']
        except KeyError as e:
            return render_template('error.html', message=f"Thiếu thông tin: {str(e)}."), 400

        try:
            start_dt = datetime.strptime(time, '%Y-%m-%dT%H:%M')
            end_dt = start_dt + timedelta(hours=1)
        except ValueError as e:
            return render_template('error.html',
                                   message="Định dạng thời gian không hợp lệ. Vui lòng sử dụng định dạng YYYY-MM-DDThh:mm."), 400

        time_slot = DateTimeRange(start_dt, end_dt)
        user = User.find_by_id(session['user']['id'])
        booking = user.bookRoom(space, time_slot)
        if booking:
            space.status = 'reserved'
            space.timeSlot = time_slot
            booking.confirm()
            return redirect(url_for('reservation.success'))
        return render_template('error.html', message="Đặt phòng thất bại. Vui lòng thử lại."), 400

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
    # space = Room.find_by_id(space_id)
    # # Find the booking for this space
    # booking = next((b for b in user.bookings if b.room.roomID == space_id and b.status == "confirmed"), None)
    

    return render_template('checkin.html', space=None, booking=None, message=None, error=None)

@reservation_bp.route('/success')
def success():
    return render_template('success.html', message="Reservation successful. QR code sent to email.")


@reservation_bp.route('/auto_cancel')
def auto_cancel():
    # from datetime import datetime
    # for booking in Booking.all():
    #     if booking.timeSlot.startTime < datetime.now() and booking.status == "pending":
    #         booking.cancel()
    #         print(f"Auto-canceled booking {booking.bookingID}")
    return render_template('cancel.html', booking=None)
