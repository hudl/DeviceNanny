from flask import Blueprint, jsonify
from deviceNanny.usb_checkout import *
from deviceNanny.db_actions import *

from deviceNanny.db import get_db

bp = Blueprint('api', __name__, url_prefix='/api')


@bp.route('devices', methods=['GET'])
def devices():
    db = get_db()
    rows = db.execute('SELECT * FROM devices').fetchall()
    data = [dict(row) for row in rows]
    return jsonify(data)


@bp.route('devices/detected', methods=['GET'])
def device_detected():
    # logging.debug("[usb_checkout] STARTED")
    # timer = multiprocessing.Process(target=timeout, name="Timer", args=(30,))
    location = "Test"
    # logging.info("LOCATION: {}".format(location))
    port = find_port()
    serial = get_serial(port)
    device_id = get_device_id_from_serial(serial)
    device_name = get_device_name(device_id, location, port)
    filename = create_tempfile(port)
    play_sound()
    if device_id is None and serial is not None:
        add_device(serial)
    else:
        checked_out = check_if_out(location, port)
        if checked_out:
            check_in_device(location, device_id, port)
        else:
            checkout_device(location, port)
    print("------------DEVICE DETECTED-----------")
    delete_tempfile(filename)
    return "DEVICE DETECTED"


@bp.route('devices/add', methods=['POST'])
def add_device(serial):
    to_database(serial)


@bp.route('devices/checkout', methods=['PUT'])
def checkout_device(location, port):
    logging.info("[usb_checkout][main] CHECK OUT")
    timer = multiprocessing.Process(target=timeout, name="Timer", args=(30,))
    device_id = get_device_id_from_port(location, port)
    device_name = get_device_name_from_id(location, device_id)
    timer.start()
    user_info = get_user_info()
    check_out(user_info, device_id)
    slack.check_out_notice(user_info, device_name)
    logging.info(
        "[usb_checkout][main] {} checked out by {} {}.".format(
            device_name,
            user_info.get('FirstName'), user_info.get('LastName')))


@bp.route('devices/check-in', methods=['PUT'])
def check_in_device(location, device_id, port):
    logging.info("[usb_checkout][main] CHECK IN")
    device_name = get_device_name_from_id(location, device_id)
    user_info = get_user_info_from_db(device_id)
    check_in(device_id, port)
    slack.check_in_notice(user_info, device_name)
