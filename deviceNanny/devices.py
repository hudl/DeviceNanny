import csv

from flask import Blueprint, render_template, redirect, url_for, flash

from deviceNanny.db import get_db
from deviceNanny.forms import SingleDeviceForm, UploadFileForm

bp = Blueprint('devices', __name__, url_prefix='/devices')


@bp.route('/add', methods=('GET', 'POST'))
def add():
    add_single_device = SingleDeviceForm()
    upload_file = UploadFileForm()
    db = get_db()
    if add_single_device.validate_on_submit():
        device_id = add_single_device.device_id.data
        device_name = add_single_device.device_name.data
        serial_udid = add_single_device.serial_udid.data
        manufacturer = add_single_device.manufacturer.data
        model = add_single_device.model.data
        device_type = add_single_device.device_type.data
        office = add_single_device.office.data

        error = None
        if not device_id:
            error = 'Device ID is required'
        elif not device_name:
            error = 'Device name is required'
        elif not serial_udid:
            error = 'Serial UDID id is required'
        elif not manufacturer:
            error = 'Manufacturer is required'
        elif not model:
            error = 'Model is required'
        elif not device_type:
            error = 'Type is required'
        elif not office:
            error = 'Office location is required'
        elif db.execute(
            'SELECT id FROM devices WHERE serial_udid = ?', (serial_udid,)
        ).fetchone() is not None:
            error = 'Device with udid {} is already in DeviceNanny'.format(serial_udid)

        if error is None:
            db.execute(
            'INSERT INTO devices (device_id, device_name, serial_udid, manufacturer, model, device_type, office) VALUES (?,?,?,?,?,?,?)',
                (device_id, device_name, serial_udid, manufacturer, model, device_type, office)
            )
            db.commit()
            return redirect(url_for('devices.add'))

        flash(error)

    if upload_file.validate_on_submit():
        file = upload_file.file.data
        print(file)
        content = file.read().decode('utf-8')

        reader = csv.reader(content.splitlines(), delimiter=',')
        columns = next(reader)
        insert_query = 'INSERT INTO devices({}) VALUES ({})'.format(','.join(columns), ','.join('?' * len(columns)))
        select_query = 'SELECT serial_udid FROM devices WHERE serial_udid = ?'
        cursor = db.cursor()
        for device_data in reader:
            print(device_data)
            # TODO make this a little smarter
            if db.execute(select_query, (device_data[2],)).fetchone() is None:
                cursor.execute(insert_query, device_data)

        db.commit()
        file.close()

    return render_template('add_devices.html',
                           title="Add Devices",
                           add_single_device=add_single_device,
                           upload_file=upload_file)