from flask import Blueprint, render_template, request, redirect, url_for, session, jsonify
from models.study_space import Room, DateTimeRange
from models.user import User, Student
from models.reservation import Booking
from data.database import get_db
from datetime import datetime, timedelta
from sqlalchemy.orm import joinedload
import json
import qrcode
import qrcode.image.pil
import io
import base64
import os
import time

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
        end = start + timedelta(hours=1/600)
        criteria['timeSlot'] = DateTimeRange(startTime=start, endTime=end)
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

    # Pages for multiple rooms
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
            end_dt = start_dt + timedelta(hours=1/60/10)
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
        print("\nTimeslot:", time_slot.to_string())
        if booking:
            # Ensure booking is added to the session and committed to get bookingID
            db.add(booking)
            db.commit()  # Commit to assign bookingID
            if booking.bookingID is None:
                print("Booking ID is None after commit")
                db.close()
                return render_template('error.html', message="Lỗi khi tạo đặt phòng: bookingID không được gán."), 500

            space.updateStatus('reserved')
            space.updateTimeSlot(time_slot)
            booking.status = "confirmed"  # Ensure booking is confirmed
            print(f"Booking ID: {booking.bookingID}")
            print(f"Booking QR Code: {booking.qrCode}")

            # Generate QR code
            qr_code_data = str(booking.qrCode)
            try:
                qr = qrcode.QRCode(version=1, box_size=5, border=2)
                qr.add_data(qr_code_data)
                qr.make(fit=True)
                img = qr.make_image(fill='black', back_color='white')

                # Convert to base64 for immediate rendering
                buffered = io.BytesIO()
                img.save(buffered, format="PNG")
                qr_base64 = base64.b64encode(buffered.getvalue()).decode('utf-8')
                qr_data_uri = f"data:image/png;base64,{qr_base64}"

                # Save QR code to filesystem
                booking_id = booking.bookingID
                qr_image_path = os.path.join('views', 'static', 'qrcodes', f'qr_{booking_id}.png')
                os.makedirs(os.path.dirname(qr_image_path), exist_ok=True)
                img.save(qr_image_path)
                print(f"QR image saved to: {qr_image_path}")

                # Ensure the file is fully written (optional since rendering uses base64)
                max_attempts = 10
                attempt = 0
                while not os.path.exists(qr_image_path) and attempt < max_attempts:
                    time.sleep(0.1)  # Wait 100ms per attempt
                    attempt += 1
                if not os.path.exists(qr_image_path):
                    print(f"QR image not found after {max_attempts} attempts - proceeding with base64 rendering")
                    # Continue anyway since we're using base64 for rendering

            except Exception as e:
                print(f"Error generating QR code: {e}")
                db.close()
                return render_template('error.html', message=f"Failed to generate QR code: {str(e)}"), 500

            db.commit()
            db.close()
            return redirect(
                url_for('reservation.success', qr_image=qr_data_uri, qr_code=qr_code_data))
        db.close()
        return render_template('error.html', message="Đặt phòng thất bại. Vui lòng thử lại."), 400

    db.close()
    return render_template('reservation.html', space=space)


@reservation_bp.route('/cancel/<space_id>', methods=['GET', 'POST'])
def cancel_reservation(space_id):
    if 'user' not in session:
        print("No user in session, returning JSON error for cancellation")  # Debug log
        return jsonify({'error': 'Phiên đăng nhập không hợp lệ. Vui lòng đăng nhập lại.'}), 401

    db = next(get_db())
    space = db.query(Room).filter_by(roomID=space_id).first()
    if not space:
        db.close()
        print(f"Room {space_id} not found during cancellation")  # Debug log
        return jsonify({'error': 'Không tìm thấy phòng.'}), 404

    user = db.query(Student).filter_by(userID=session['user']['id']).first()
    if not user:
        db.close()
        print("User not found or not a student during cancellation")  # Debug log
        return jsonify({'error': 'Chỉ sinh viên mới có thể huỷ.'}), 403

    booking = db.query(Booking).filter_by(room_id=space_id, student_id=user.userID, status="confirmed").first()
    if not booking:
        db.close()
        print(f"No confirmed booking found for room {space_id} and user {user.userID}")  # Debug log
        return jsonify({'error': 'Bạn không có đặt phòng này hoặc đã huỷ.'}), 404

    if request.method == 'POST':
        try:
            booking.status = "cancelled"
            space.updateStatus("available")
            space.updateTimeSlot(None)
            db.commit()
            print(f"Successfully canceled booking {booking.bookingID} for room {space_id}")  # Debug log
            db.close()
            return jsonify({'message': 'Hủy đặt phòng thành công!', 'redirect': url_for('reservation.dashboard')}), 200
        except Exception as e:
            db.rollback()
            print(f"Error canceling booking: {e}")  # Debug log
            db.close()
            return jsonify({'error': f'Lỗi khi hủy đặt phòng: {str(e)}'}), 500

    db.close()
    return render_template('cancel.html', space=space, booking=booking)



@reservation_bp.route('/checkin/<space_id>', methods=['GET', 'POST'])
def checkin(space_id):
    if 'user' not in session:
        return jsonify({'error': 'Phiên đăng nhập không hợp lệ. Vui lòng đăng nhập lại.'}), 401

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

        print(f"Received QR code from client: '{qr_code}'")
        if not qr_code:
            db.close()
            return jsonify({'error': 'Mã QR không được cung cấp.'}), 400

        if not booking.qrCode:
            print("Booking has no QR code assigned.")
            db.close()
            return jsonify({'error': 'Đặt phòng không có mã QR hợp lệ.'}), 400

        # Normalize QR codes for comparison (trim whitespace, ignore case)
        qr_code = qr_code.strip()
        booking_qr_code = booking.qrCode.strip()
        print(f"Comparing QR code: '{qr_code}' with booking QR code: '{booking_qr_code}'")
        if qr_code == booking_qr_code:
            print(f"QR code match successful. Attempting check-in for user {user.userID}.")
            if qr_code == booking_qr_code:
                print(f"QR code match successful. Attempting check-in for user {user.userID}.")
                if user.checkIn(qr_code):
                    space.updateStatus('in_use')
                    booking.status = "completed"
                    db.commit()
                    print(f"Check-in successful for booking {booking.bookingID}. Room {space_id} set to in_use.")
                    db.close()
                    return jsonify({'message': 'Check-in thành công!', 'redirect': url_for('reservation.checkin_success')}), 200
            print("Check-in failed in user.checkIn method.")
            db.close()
            return jsonify({'error': 'Check-in thất bại. Vui lòng thử lại.'}), 400
        print("QR code mismatch.")
        db.close()
        return jsonify({'error': 'Mã QR không hợp lệ.'}), 400

    db.close()
    return render_template('checkin.html', space=space, booking=booking, message=None, error=None)


@reservation_bp.route('/checking')
def checkin_success():
    return render_template('checkin_success.html', message="Checkin successful. Remember to return on time.")


@reservation_bp.route('/success')
def success():
    qr_image = request.args.get('qr_image')
    qr_code = request.args.get('qr_code')  # Retrieve the qr_code value
    print(f"Rendering success page with qr_code: {qr_code}")  # Debug print
    return render_template('success.html', message="Reservation successful. QR code sent to email.", qr_image=qr_image,
                           qr_code=qr_code)


@reservation_bp.route('/auto_cancel')
def auto_cancel():
    if 'user' not in session or session['user']['role'] != 'admin':
        return redirect(url_for('auth.login'))

    db = next(get_db())
    bookings = db.query(Booking).all()  # Check all bookings, not just pending
    current_time = datetime.now()
    for booking in bookings:
        if booking.status in ["confirmed",
                              "completed"] and booking.timeSlot and booking.timeSlot.endTime < current_time:
            if booking.room:
                booking.room.updateStatus('available')
                booking.room.updateTimeSlot(None)
                if booking.status == "confirmed":
                    booking.cancel()  # Cancel if still confirmed
                elif booking.status == "completed":
                    db.delete(booking)  # Remove completed booking if time has passed
                print(f"Booking {booking.bookingID} ended. Room {booking.room.roomID} set to available.")
            db.commit()
    db.close()
    return redirect(url_for('reservation.dashboard'))