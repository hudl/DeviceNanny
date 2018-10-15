from flask import Blueprint, jsonify

from deviceNanny.db import get_db

bp = Blueprint('api', __name__, url_prefix='/api')


@bp.route('devices', methods=['GET'])
def devices():
    db = get_db()
    rows = db.execute('SELECT * FROM devices').fetchall()
    data = [dict(row) for row in rows]
    return jsonify(data)


# @bp.route('devices/checkout', methods='POST')
# def checkout_device():
