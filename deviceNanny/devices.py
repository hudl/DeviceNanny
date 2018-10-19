import csv

from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_table import Table, Col, LinkCol

from deviceNanny.db import get_db
from deviceNanny.forms import SingleDeviceForm, UploadFileForm

bp = Blueprint('devices', __name__, url_prefix='/devices')


class DevicesTable(Table):
    html_attrs = {'class': 'table table-hover'}
    device_name = Col("Device Name")
    serial_udid = Col("Serial UDID")
    delete_device = LinkCol('Delete Device',
                            'devices.delete_device',
                            url_kwargs=dict(id='id'),
                            anchor_attrs={'class': 'btn btn-danger btn-sm'},
                            allow_sort=False)

    def get_tr_attrs(self, item):
        if int(item['id']) % 2 == 0:
            return {'class': 'table-primary'}
        else:
            return {'class': 'table-secondary'}


@bp.route('/manage', methods=('GET', 'POST'))
def manage():
    add_single_device = SingleDeviceForm()
    upload_file = UploadFileForm()
    db = get_db()
    device_data = db.execute("SELECT id, device_name, substr(serial_udid, 1, 7) || '...' as serial_udid FROM devices").fetchall()
    table = DevicesTable(device_data)

    if add_single_device.validate_on_submit():
        device_id = add_single_device.device_id.data
        device_name = add_single_device.device_name.data
        serial_udid = add_single_device.serial_udid.data
        manufacturer = add_single_device.manufacturer.data
        model = add_single_device.model.data
        os_version = add_single_device.os_version.data
        device_type = add_single_device.device_type.data
        location = add_single_device.location.data

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
        elif not os_version:
            error = 'OS Version is required'
        elif not location:
            error = 'Office location is required'
        elif db.execute(
            'SELECT id FROM devices WHERE serial_udid = ?', (serial_udid,)
        ).fetchone() is not None:
            error = 'Device with udid {} is already in DeviceNanny'.format(serial_udid)

        if error is None:
            db.execute(
            'INSERT INTO devices (device_id, device_name, serial_udid, manufacturer, model, device_type, os_version, location) VALUES (?,?,?,?,?,?,?,?)',
                (device_id, device_name, serial_udid, manufacturer, model, device_type, os_version, location)
            )
            db.commit()
            flash('Successfully added device with serial udid {}'.format(serial_udid))
            return redirect(url_for('devices.manage'))

        flash(error)

    if upload_file.validate_on_submit():
        file = upload_file.file.data
        content = file.read().decode('utf-8')

        reader = csv.reader(content.splitlines(), delimiter=',')
        columns = next(reader)
        insert_query = 'INSERT INTO devices({}) VALUES ({})'.format(','.join(columns), ','.join('?' * len(columns)))
        select_query = 'SELECT serial_udid FROM devices WHERE serial_udid = ?'
        cursor = db.cursor()
        for device_data in reader:
            # TODO make this a little smarter
            if db.execute(select_query, (device_data[2],)).fetchone() is None:
                cursor.execute(insert_query, device_data)

        db.commit()
        flash('Successfully imported devices from csv')
        file.close()
        return redirect(url_for('devices.manage'))

    return render_template('manage_devices.html',
                           title="Manage Devices",
                           table=table,
                           add_single_device=add_single_device,
                           upload_file=upload_file)


@bp.route('/delete_device')
def delete_device():
    db = get_db()
    device_id = request.args['id']
    row = db.execute('SELECT device_name, serial_udid FROM devices WHERE id = {}'.format(device_id)).fetchone()
    db.execute('DELETE FROM devices WHERE id = {}'.format(device_id))
    db.commit()
    flash("Successfully deleted device {} with serial udid {}".format(row['device_name'], row['serial_udid']))
    return redirect(url_for('devices.manage'))