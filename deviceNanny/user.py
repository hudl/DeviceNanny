import csv

from flask import Blueprint, render_template, redirect, url_for, flash, current_app, request
from flask_table import Table, Col, LinkCol

from deviceNanny.db import get_db
from deviceNanny.forms import SingleUserForm, UploadFileForm

bp = Blueprint('user', __name__, url_prefix='/user')


class UsersTable(Table):
    html_attrs = {'class': 'table table-hover'}
    first_name = Col('First Name')
    last_name = Col('Last Name')
    delete_user = LinkCol('Delete User',
                          'user.delete_user',
                          url_kwargs=dict(id='id'),
                          anchor_attrs={'class': 'btn btn-primary btn-sm'},
                          allow_sort=False)

    def get_tr_attrs(self, item):
        if int(item['id']) % 2 == 0:
            return {'class': 'table-primary'}
        else:
            return {'class': 'table-secondary'}


@bp.route('/manage', methods=('GET', 'POST'))
def manage():
    add_single_user = SingleUserForm()
    upload_file = UploadFileForm()
    db = get_db()

    user_data = db.execute('SELECT id, first_name, last_name FROM users WHERE id != 1 AND id != 2')
    table = UsersTable(user_data)

    if add_single_user.validate_on_submit():
        first_name = add_single_user.first_name.data
        last_name = add_single_user.last_name.data
        slack_id = add_single_user.slack_id.data

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

        if error is None:
            db.execute(
            'INSERT INTO users (first_name, last_name, slack_id, location) VALUES (?,?,?,?)',
                (first_name, last_name, slack_id, current_app.config['location'])
            )
            db.commit()
            flash('Successfully added user {} {}'.format(first_name, last_name))
            return redirect(url_for('user.manage'))

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
        flash('Successfully imported users from csv')
        file.close()
        return redirect(url_for('user.manage'))

    return render_template('manage_user.html',
                           title='Manage Users',
                           table=table,
                           add_single_user=add_single_user,
                           upload_file=upload_file)


@bp.route('/delete_user')
def delete_user():
    db = get_db()
    user_id = request.args['id']
    row = db.execute("SELECT first_name || ' ' || last_name as user_name FROM users WHERE id = {}".format(user_id)).fetchone()
    db.execute('DELETE FROM users WHERE id = {}'.format(user_id))
    db.commit()
    flash("Successfully deleted user {}".format(row['user_name']))
    return redirect(url_for('user.manage'))
