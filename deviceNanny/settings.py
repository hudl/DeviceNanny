from flask import Blueprint, render_template, url_for
from werkzeug.utils import redirect

from deviceNanny.db import get_db
from deviceNanny.forms import SettingsForm

bp = Blueprint('settings', __name__, url_prefix='/settings')


@bp.route('/update', methods=('GET', 'POST'))
def update():
    settings = SettingsForm()
    db = get_db()
    settings_data = db.execute(
        'SELECT * FROM settings WHERE id = 1'
    ).fetchone()

    if settings.validate_on_submit():
        slack_channel = settings.slack_channel.data
        slack_team_channel = settings.slack_team_channel.data
        reminder_interval = settings.reminder_interval.data
        checkout_length = settings.checkout_length.data
        office_location = settings.office_location.data
        message = settings.message.data

        insert_query = 'UPDATE settings SET {} = "{}" WHERE id = 1'

        if slack_channel:
            db.execute(insert_query.format('slack_channel', slack_channel))
        if slack_team_channel:
            db.execute(insert_query.format('slack_team_channel', slack_team_channel))
        if reminder_interval:
            db.execute(insert_query.format('reminder_interval', reminder_interval))
        if checkout_length:
            db.execute(insert_query.format('checkout_length', checkout_length))
        if office_location:
            db.execute(insert_query.format('office_location', office_location))
        if message:
            db.execute(insert_query.format('message', message))

        db.commit()
        return redirect(url_for('settings.update'))

    return render_template('settings.html',
                           settings=settings,
                           settings_data=settings_data)
