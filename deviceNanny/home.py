from flask import Blueprint, render_template, request, url_for, flash
from flask_table import Table, Col, LinkCol
from werkzeug.utils import redirect

from deviceNanny.db import get_db

bp = Blueprint('home', __name__, url_prefix='/')


class DeviceTable(Table):
    html_attrs = {'class': 'table table-hover'}
    device_name = Col('Device Name')
    manufacturer = Col('Manufacture')
    model = Col('Model')
    device_type = Col('Device Type')
    os_version = Col('OS Version')
    user_name = Col('Checked Out By')
    extend_checkout = LinkCol('Extend Checkout', 'home.extend_checkout', url_kwargs=dict(id='id'), anchor_attrs={'class': 'btn btn-primary btn-sm'})

    def get_tr_attrs(self, item):
        if int(item['id']) % 2 == 0:
            return {'class': 'table-primary'}
        else:
            return {'class': 'table-secondary'}


@bp.route('/')
def home():
    db = get_db()
    rows = db.execute(
        "SELECT devices.id, devices.device_name, devices.manufacturer, devices.model, devices.device_type, devices.os_version, users.first_name || ' ' || users.last_name as user_name "
        "FROM devices INNER JOIN users ON devices.checked_out_by=users.id"
    ).fetchall()

    table = DeviceTable(rows)

    return render_template('home.html', table=table)


@bp.route('/extend_checkout')
def extend_checkout():
    db = get_db()
    row = db.execute('SELECT time_checked_out FROM devices WHERE id = {}'.format(request.args['id'])).fetchone()
    new_time = row['time_checked_out'] + 3600
    upload_query = 'UPDATE devices SET time_checked_out = {} WHERE id = {}'
    db.execute(upload_query.format(new_time, request.args['id']))
    db.commit()
    flash('Successfully extended your checkout time by 1 hour')
    return redirect(url_for('home.home'))
