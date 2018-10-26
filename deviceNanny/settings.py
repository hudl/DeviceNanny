from flask import Blueprint, render_template, url_for, current_app, flash
from werkzeug.utils import redirect

from deviceNanny.db import get_db
from deviceNanny.forms import SettingsForm

bp = Blueprint('settings', __name__, url_prefix='/settings')


@bp.route('/update', methods=('GET', 'POST'))
def update():
    db = get_db()
    settings_data = db.execute(
        'SELECT * FROM settings WHERE id = 1'
    ).fetchone()
    settings = SettingsForm(slack_channel=settings_data['slack_channel'],
                            slack_team_channel=settings_data['slack_team_channel'],
                            reminder_interval=settings_data['reminder_interval'],
                            checkout_expires=settings_data['checkout_expires'],
                            office_location=settings_data['office_location'])
    if settings.validate_on_submit():
        slack_channel = settings.slack_channel.data
        slack_team_channel = settings.slack_team_channel.data
        reminder_interval = settings.reminder_interval.data
        checkout_expires = settings.checkout_expires.data
        office_location = settings.office_location.data

        update_query = 'UPDATE settings SET {} = "{}" WHERE id = 1'

        if slack_channel:
            current_app.config['slack_channel'] = settings_data['slack_channel']
            db.execute(update_query.format('slack_channel', slack_channel))
        if slack_team_channel:
            current_app.config['slack_team_channel'] = settings_data['slack_team_channel']
            db.execute(update_query.format('slack_team_channel', slack_team_channel))
        if reminder_interval:
            current_app.config['reminder_interval'] = settings_data['reminder_interval']
            db.execute(update_query.format('reminder_interval', reminder_interval))
        if checkout_expires:
            current_app.config['checkout_expires'] = settings_data['checkout_expires']
            db.execute(update_query.format('checkout_expires', checkout_expires))
        if office_location:
            current_app.config['location'] = settings_data['office_location']
            db.execute(update_query.format('office_location', office_location))

        db.commit()
        flash('Successfully updated DeviceNanny Settings', 'alert alert-success')
        return redirect(url_for('settings.update'))

    return render_template('settings.html',
                           settings=settings,
                           settings_data=settings_data)
