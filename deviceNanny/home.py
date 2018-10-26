from flask import Blueprint, render_template, request, url_for, flash
from flask_table import Table, Col, LinkCol
from werkzeug.utils import redirect

from deviceNanny.db import get_db
from deviceNanny.usb_checkout import get_user_info_from_popup

bp = Blueprint('home', __name__, url_prefix='/')


class DeviceTable(Table):
    html_attrs = {'class': 'table table-hover'}
    device_name = Col('Device Name')
    manufacturer = Col('Manufacture')
    model = Col('Model')
    device_type = Col('Device Type')
    os_version = Col('OS Version')
    user_name = Col('Checked Out By')
    requested_by = Col('Requested By')
    extend_checkout = LinkCol('Extend Checkout',
                              'home.extend_checkout',
                              url_kwargs=dict(id='id'),
                              anchor_attrs={'class': 'btn btn-warning btn-sm'},
                              allow_sort=False)
    requested_device = LinkCol('Request Device',
                               'home.request_device',
                               url_kwargs=dict(id='id'),
                               anchor_attrs={'class': 'btn btn-info btn-sm'},
                               allow_sort=False)

    allow_sort = True

    def sort_url(self, col_key, reverse=False):
        if reverse:
            direction = 'desc'
        else:
            direction = 'asc'
        return url_for('home.home', sort=col_key, direction=direction)

    def get_tr_attrs(self, item):
        checked_out_by = item['user_name'].lower()
        if checked_out_by != "- -" and checked_out_by != "missing device":
            return {'class': 'table-success'}
        elif checked_out_by == "missing device":
            return {'class': 'table-danger'}
        elif int(item['row_number']) % 2 == 0:
            return {'class': 'table-primary'}
        else:
            return {'class': 'table-secondary'}


@bp.route('/')
def home():
    sort = request.args.get('sort', 'id')
    direction = request.args.get('direction')
    reverse = (request.args.get('direction', 'asc') == 'desc')
    query = "SELECT devices.id, devices.device_name, devices.manufacturer, devices.model, devices.device_type, " \
            "devices.os_version, users.first_name || ' ' || users.last_name as user_name, devices.requested_by " \
            "FROM devices INNER JOIN users ON devices.checked_out_by=users.id"
    if direction:
        if sort == "user_name":
            sort = "user_name"
        else:
            sort = "devices.{}".format(sort)

        query = "{} ORDER BY {} {}".format(query, sort, request.args['direction'].upper())
    else:
        query = "{} ORDER BY devices.checked_out_by, devices.device_type, devices.os_version, devices.manufacturer, devices.model".format(query)

    print(query)
    db = get_db()

    rows = db.execute(query).fetchall()

    data_row = []
    for idx, r in enumerate(rows):
        data = {}
        data['id'] = r['id']
        data['device_name'] = r['device_name']
        data['manufacturer'] = r['manufacturer']
        data['model'] = r['model']
        data['device_type'] = r['device_type']
        data['os_version'] = r['os_version']
        data['user_name'] = r['user_name']
        data['row_number'] = idx
        data_row.append(data)

    table = DeviceTable(data_row, sort_by=sort, sort_reverse=reverse)

    return render_template('home.html', table=table)


@bp.route('/extend_checkout')
def extend_checkout():
    db = get_db()
    row = db.execute('SELECT time_checked_out FROM devices WHERE id = {}'.format(request.args['id'])).fetchone()
    new_time = row['time_checked_out'] + 3600
    upload_query = 'UPDATE devices SET time_checked_out = {} WHERE id = {}'
    db.execute(upload_query.format(new_time, request.args['id']))
    db.commit()
    flash('Successfully extended your checkout time by 1 hour', 'alert alert-success')
    return redirect(url_for('home.home'))


@bp.route('/request_device')
def request_device():
    db = get_db()
    user = get_user_info_from_popup('Request Device')
    upload_query = 'UPDATE devices SET requested_by = {} WHERE id = {}'
    db.execute(upload_query.format(user['id'], request.args['id']))
    db.commit()
    flash('Successfully requested the device', 'alert alert-success')
    return redirect(url_for('home.home'))
