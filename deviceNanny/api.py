from flask import Blueprint, jsonify, current_app

from deviceNanny.db import get_db

bp = Blueprint('api', __name__, url_prefix='/api')


@bp.route('devices', methods=['GET'])
def devices():
    current_app.logger.info("Getting all devices")
    db = get_db()
    rows = db.execute('SELECT * FROM devices').fetchall()
    data = [dict(row) for row in rows]
    return jsonify(data)


@bp.route('devices/detected', methods=['GET'])
def device_detected():
    # logging.debug("[usb_checkout] STARTED")
    timer = multiprocessing.Process(target=timeout, name="Timer", args=(30,))
    location = "Test"
    # logging.info("LOCATION: {}".format(location))
    port = find_port()
    serial = get_serial(port)
    device_id = db.get_device_id_from_serial(serial)
    device_name = get_device_name(device_id, location, port)
    filename = create_tempfile(port)
    play_sound()
    print("------------DEVICE DETECTED-----------")
    return "DEVICE DETECTED"