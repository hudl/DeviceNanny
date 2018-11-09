from flask import Blueprint, render_template, request, url_for, flash
from flask_table import Table, Col, LinkCol
from flask_table.html import element
from werkzeug.utils import redirect

from deviceNanny.db import get_db

bp = Blueprint('home', __name__, url_prefix='/')


# Subclass the LinkCol class to override anchor attrs
class ExtendCol(LinkCol):

    def __init__(self, name, endpoint, attr=None, attr_list=None,
                 url_kwargs=None, url_kwargs_extra=None,
                 anchor_attrs=None, text_fallback=None, **kwargs):
        super(LinkCol, self).__init__(
            name,
            attr=attr,
            attr_list=attr_list,
            **kwargs)
        self.endpoint = endpoint
        self._url_kwargs = url_kwargs or {}
        self._url_kwargs_extra = url_kwargs_extra or {}
        self.text_fallback = text_fallback
        self.anchor_attrs = anchor_attrs or {}

    def td_contents(self, item, attr_list):
        class_name = 'btn btn-warning btn-sm'
        attrs = dict(href=self.url(item))
        if item['user_name'].lower() == "- -":
            self.anchor_attrs = {'class': '{} disabled'.format(class_name)}
        else:
            self.anchor_attrs = {'class': class_name}

        attrs.update(self.anchor_attrs)
        text = self.td_format(self.text(item, attr_list))
        return element('a', attrs=attrs, content=text, escape_content=False)


class DeviceTable(Table):
    html_attrs = {'class': 'table table-hover'}
    device_name = Col('Device Name')
    manufacturer = Col('Manufacture')
    model = Col('Model')
    device_type = Col('Device Type')
    os_version = Col('OS Version')
    user_name = Col('Checked Out By')
    extend_checkout = ExtendCol(name='Extend Checkout',
                              endpoint='home.extend_checkout',
                              url_kwargs=dict(id='id'),
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
            return {'class': 'table-dark'}
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
    query = "SELECT devices.id, devices.device_name, devices.manufacturer, devices.model, devices.device_type, devices.os_version, users.first_name || ' ' || users.last_name as user_name " \
            "FROM devices INNER JOIN users ON devices.checked_out_by=users.id"
    if direction:
        if sort == "user_name":
            sort = "user_name"
        else:
            sort = "devices.{}".format(sort)

        query = "{} ORDER BY {} {}".format(query, sort, request.args['direction'].upper())
    else:
        query = "{} ORDER BY devices.checked_out_by, devices.device_type, devices.os_version, devices.manufacturer, devices.model".format(query)

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
