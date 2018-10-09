from flask import Blueprint, render_template, request, redirect, url_for, flash

from deviceNanny.db import get_db

bp = Blueprint('devices', __name__, url_prefix='/devices')


@bp.route('/add', methods=('GET', 'POST'))
def add():
    if request.method == 'POST':
        device_id = request.form['device_id']
        device_name = request.form['device_name']
        serial_udid = request.form['serial_udid']
        manufacturer = request.form['manufacturer']
        model = request.form['model']
        device_type = request.form['device_type']
        os = request.form['os']
        office = request.form['office']

        db = get_db()
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
        elif not os:
            error = 'Operating System is required'
        elif not office:
            error = 'Office location is required'
        elif db.execute(
            'SELECT id FROM devices WHERE serial_udid = ?', (serial_udid,)
        ).fetchone() is not None:
            error = 'Device with udid {} is already in DeviceNanny'.format(serial_udid)

        if error is None:
            db.execute(
            'INSERT INTO devices (device_id, device_name, serial_udid, manufacturer, model, device_type, os, office) VALUES (?,?,?,?,?,?,?,?)',
                (device_id, device_name, serial_udid, manufacturer, model, device_type, os, office)
            )
            db.commit()
            return redirect(url_for('devices.add'))

        flash(error)

    return render_template('add_devices.html')