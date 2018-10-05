from flask import Blueprint, render_template
from flask_table import Table, Col

from deviceNanny.db import get_db

bp = Blueprint('home', __name__, url_prefix='/')


class DeviceTable(Table):
    html_attrs = {'class': 'table table-hover'}
    device_id = Col('Device Id')
    device_name = Col('Device Name')
    serial_udid = Col('Serial UDID')
    manufacturer = Col('Manufacture')
    model = Col('Model')
    device_type = Col('Device Type')
    os = Col('OS')
    checked_out_by = Col('Checked out by')
    office = Col('Office Location')

    def get_tr_attrs(self, item):
        if int(item['id']) % 2 == 0:
            return {'class': 'table-primary'}
        else:
            return {'class': 'table-secondary'}


@bp.route('/')
def home():
    db = get_db()
    rows = db.execute(
        'SELECT id, device_id, device_name, serial_udid, manufacturer, model, device_type, os, checked_out_by, office FROM devices'
    ).fetchall()
    table = DeviceTable(rows)
    return render_template('home.html', table=table)
