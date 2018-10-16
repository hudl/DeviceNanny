import csv

from flask import Blueprint, render_template, redirect, url_for, flash

from deviceNanny.db import get_db
from deviceNanny.forms import SingleUserForm, UploadFileForm

bp = Blueprint('user', __name__, url_prefix='/user')


@bp.route('/add', methods=('GET', 'POST'))
def add():
    add_single_user = SingleUserForm()
    upload_file = UploadFileForm()
    db = get_db()

    if add_single_user.validate_on_submit():
        first_name = add_single_user.first_name.data
        last_name = add_single_user.last_name.data
        slack_id = add_single_user.slack_id.data
        location = add_single_user.location.data

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

        if not location:
            location = None

        if error is None:
            db.execute(
            'INSERT INTO users (first_name, last_name, slack_id, location) VALUES (?,?,?,?)',
                (first_name, last_name, slack_id, location)
            )
            db.commit()
            return redirect(url_for('user.add'))

        flash(error)

    if upload_file.validate_on_submit():
        file = upload_file.file.data

        content = file.read().decode('utf-8')

        reader = csv.reader(content.splitlines(), delimiter=',')
        columns = next(reader)
        insert_query = 'INSERT INTO users({}) VALUES ({})'.format(','.join(columns), ','.join('?' * len(columns)))
        select_query = 'SELECT first_name, last_name FROM users WHERE first_name = ? AND last_name = ?'
        cursor = db.cursor()
        for user_data in reader:
            # TODO make this a little smarter
            if db.execute(select_query, (user_data[0], user_data[1])).fetchone() is None:
                cursor.execute(insert_query, user_data)

        db.commit()
        file.close()
        return redirect(url_for('user.add'))

    return render_template('add_user.html',
                           title='Add Users',
                           add_single_user=add_single_user,
                           upload_file=upload_file)
