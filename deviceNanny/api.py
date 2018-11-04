import deviceNanny.usb_checkout as usb_checkout
import deviceNanny.nanny as nanny
import deviceNanny.db_actions as db_actions
from deviceNanny.slack import NannySlacker
import multiprocessing

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
    location = current_app.config['location']
    port = usb_checkout.find_port()
    serial = usb_checkout.get_serial(port)
    device_id = db_actions.get_device_id_from_serial(serial)
    device_name = db_actions.get_device_name(location, port)
    filename = usb_checkout.create_tempfile(port, device_name)
    if filename:
        usb_checkout.play_sound()
        if device_id is None and serial is not None:
            add_device(serial, port, location, filename)
        else:
            checked_out = usb_checkout.check_if_out(location, port)
            if checked_out:
                check_in_device(device_id, port)
            else:
                checkout_device(filename, location, port)
        usb_checkout.delete_tempfile(filename)
    return "DONE"


@bp.route('devices/add', methods=['POST'])
def add_device(serial, port, location, filename):
    current_app.logger.info("[checkout_device] NEW DEVICE")
    usb_checkout.to_database(serial, port, location, filename)
    return "DONE"


@bp.route('devices/checkout', methods=['PUT'])
def checkout_device(filename, location, port):
    current_app.logger.info("[checkout_device] CHECK OUT")
    device_id = db_actions.get_device_id_from_port(location, port)
    device_name = db_actions.get_device_name_from_id(device_id)
    timer = multiprocessing.Process(target=usb_checkout.timeout, name="Timer", args=(30, port, device_id, device_name, filename))
    timer.start()
    user_info = usb_checkout.get_user_info(timer, port, device_id, device_name, filename)
    db_actions.check_out(user_info['id'], device_id)
    slacker_nanny = NannySlacker()
    slacker_nanny.check_out_notice(user_info, device_name)
    return "DONE"


@bp.route('devices/check-in', methods=['PUT'])
def check_in_device(device_id, port):
    current_app.logger.info("[check_in_device] CHECK IN")
    device_info = db_actions.get_device_info_from_id(device_id)
    user_info = usb_checkout.get_user_info_from_db(device_id)
    db_actions.check_in(device_id, port)
    nanny = NannySlacker()
    nanny.check_in_notice(user_info, device_info['device_name'])
    if device_info['requested_by']:
        requested_user_info = db_actions.get_user_info_from_id(device_info['requested_by'])
        nanny.requested_device_checked_in(requested_user_info, device_info['device_name'])
    return "DONE"


@bp.route('nanny', methods=['GET'])
def run_nanny():
    if not usb_checkout.get_pid('start_checkout'):
        nanny.clean_tmp_file()
        nanny.check_usb_connections()
        nanny.verify_registered_connections()
        nanny.checkout_reminders()
    else:
        current_app.logger.info('[run_nanny] Checkout currently in progress - skip.')
    return "NANNY DONE"


@bp.route('/device/<int:device_id>/extend_checkout/<int:time>', methods=['PUT'])
def extent_checkout(device_id, time):
    db = get_db()
    row = db.execute('SELECT time_checked_out FROM devices WHERE id = {}'.format(device_id)).fetchone()
    new_time = row['time_checked_out'] + time
    upload_query = 'UPDATE devices SET time_checked_out = {} WHERE id = {}'
    db.execute(upload_query.format(new_time, device_id))
    db.commit()

    device_data = {'device_id': device_id,
                   'old_time': row['time_checked_out'],
                   'new_time': new_time}

    return jsonify({"checkout_times": device_data})
