from flask import Blueprint
from models.iot_device import IoTDevice

iot_bp = Blueprint('iot', __name__)

@iot_bp.route('/iot/activate/<space_id>')
def activate_devices(space_id):
    devices = [d for d in IoTDevice.all() if d.room.roomID == space_id]
    for device in devices:
        device.status = "on"
        print(f"IoT: Device {device.deviceID} activated for space {space_id}")
    return "Devices activated"