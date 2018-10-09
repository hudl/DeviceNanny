from flask import Blueprint, render_template, request, redirect, url_for, flash

from deviceNanny.db import get_db

bp = Blueprint('user', __name__, url_prefix='/user')


@bp.route('/add', methods=('GET', 'POST'))
def add():
    if request.method == 'POST':
        first_name = request.form['first_name']
        last_name = request.form['last_name']
        slack_id = request.form['slack_id']
        office = request.form['office']

        db = get_db()
        error = None

        if not first_name:
            error = 'First name is required'
        elif not last_name:
            error = 'Last name is required'
        elif not slack_id:
            error = 'Slack id is required'
        elif db.execute(
            'SELECT id FROM users WHERE first_name = ? AND last_name = ?', (first_name, last_name)
        ).fetchone() is not None:
            error = 'User {} {} is already in DeviceNanny'.format(first_name, last_name)

        if not office:
            office = None

        if error is None:
            db.execute(
            'INSERT INTO users (first_name, last_name, slack_id, office) VALUES (?,?,?,?)',
                (first_name, last_name, slack_id, office)
            )
            db.commit()
            return redirect(url_for('user.add'))

        flash(error)

    return render_template('add_user.html')