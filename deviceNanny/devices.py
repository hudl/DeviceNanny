import csv
import os

from flask import Blueprint, render_template, redirect, url_for, flash, request, current_app
from flask_table import Table, Col, LinkCol

from deviceNanny.db import get_db
from deviceNanny.forms import SingleDeviceForm, UploadFileForm
from deviceNanny.db_actions import new_device_id


bp = Blueprint('devices', __name__, url_prefix='/devices')


class DevicesTable(Table):
    html_attrs = {'class': 'table table-hover'}
    device_name = Col("Device Name")
    manufacturer = Col("Manufacturer")
    model = Col("Model")
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
    device_data = db.execute("SELECT id, device_name, manufacturer, model FROM devices").fetchall()
    table = DevicesTable(device_data)

    if add_single_device.submit.data and add_single_device.validate_on_submit():
        device_id = new_device_id()
        device_name = add_single_device.device_name.data
        serial_udid = add_single_device.serial_udid.data
        manufacturer = add_single_device.manufacturer.data
        model = add_single_device.model.data
        os_version = add_single_device.os_version.data
        device_type = add_single_device.device_type.data
        location = current_app.config['location']

        error = None

        if db.execute(
            'SELECT id FROM devices WHERE serial_udid = ?', (serial_udid,)
        ).fetchone() is not None:
            error = 'Device with udid {} is already in DeviceNanny'.format(serial_udid)

        if error is None:
            db.execute(
            'INSERT INTO devices (device_id, device_name, serial_udid, manufacturer, model, device_type, os_version, '
            'location, checked_out_by) VALUES (?,?,?,?,?,?,?,?,1)',
                (device_id, device_name, serial_udid, manufacturer, model, device_type, os_version, location)
            )
            db.commit()
            flash('Successfully added device with serial udid {}'.format(serial_udid), 'alert alert-success')
            return redirect(url_for('devices.manage'))
        else:
            flash(error, 'alert alert-danger')

    if upload_file.upload_submit.data and upload_file.validate_on_submit():
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
        flash('Successfully imported devices from csv', 'alert alert-success')
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
    flash("Successfully deleted device {} with serial udid {}".format(row['device_name'], row['serial_udid']),
          'alert alert-success')
    return redirect(url_for('devices.manage'))


@bp.route('/export_devices')
def export_devices():
    db = get_db()
    cursor = db.cursor()
    cursor.execute('SELECT device_id, device_name, serial_udid, manufacturer, model, device_type, os_version, '
                   'checked_out_by, time_checked_out, last_reminded, location, port FROM devices')

    with open(os.path.join(current_app.instance_path, 'devices.csv'), "w", newline='') as csv_file:
        csv_writer = csv.writer(csv_file)
        csv_writer.writerow([i[0] for i in cursor.description])
        csv_writer.writerows(cursor)

    flash('Exported devices to {}'.format(os.path.join(current_app.instance_path, 'devices.csv')), 'alert alert-success')

    return redirect(url_for('devices.manage'))
