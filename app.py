from flask import Flask, redirect, url_for
from controllers.auth_controller import auth_bp
from controllers.reservation_controller import reservation_bp
from controllers.iot_controller import iot_bp
from models.user import Student, Admin
from models.study_space import Room

app = Flask(__name__, template_folder='views/template', static_folder='static')
app.secret_key = 's3mrs_demo'  # Required for session management

# Register blueprints for controllers
app.register_blueprint(auth_bp)
app.register_blueprint(reservation_bp)
app.register_blueprint(iot_bp)


# Initialize sample data (as per your original setup)
def init_data():
    # Create sample users
    Student("1", "Student One", "student1@hcmut.edu.vn")
    Admin("2", "Admin One", "admin1@hcmut.edu.vn")

    # Create sample rooms with equipment
    Room("P.101", "individual", 2, ["Máy chiếu", "Điều hòa"], "available", "Building A")
    Room("P.102", "group", 6, ["Máy chiếu", "Điều hòa"], "available", "Building B")
    Room("P.103", "individual", 2, ["Máy chiếu", "Điều hòa"], "available", "Building A")
    Room("P.104", "group", 6, ["Máy chiếu", "Điều hòa"], "available", "Building B")


# Initialize data on app startup
init_data()


# Root route to redirect to login
@app.route('/')
def index():
    return redirect(url_for('auth.login'))


if __name__ == '__main__':
    # Run the app on host '0.0.0.0' to be accessible on the local network
    app.run(host='0.0.0.0', port=5000, debug=True)