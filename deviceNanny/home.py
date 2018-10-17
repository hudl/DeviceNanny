from flask import Blueprint, render_template
from flask_table import Table, Col

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
