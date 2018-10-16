from flask_wtf import FlaskForm
from wtforms import StringField, RadioField, SubmitField, FileField, SelectField
from wtforms.validators import DataRequired


class SingleUserForm(FlaskForm):
    first_name = StringField('First Name', validators=[DataRequired()])
    last_name = StringField('Last Name', validators=[DataRequired()])
    slack_id = StringField('Slack ID')
    office = RadioField('Office Location',
                        choices=[('Omaha', 'Omaha'), ('Lincoln', 'Lincoln')]
                        )
    submit = SubmitField('Add')


class SingleDeviceForm(FlaskForm):
    device_id = StringField('Device Id')
    device_name = StringField('Device Name')
    serial_udid = StringField('Serial UDID')

    manufacturer_choices = [('Apple', 'Apple'),
                            ('Google', 'Google'),
                            ('Samsung', 'Samsung')]
    manufacturer = SelectField('Manufacturer', choices=manufacturer_choices)

    model_choices = [('iPhone 6s', 'iPhone 6s'),
                     ('iPhone 7', 'iPhone 7s'),
                     ('iPhone 8', 'iPhone 8'),
                     ('iPhone xX', 'iPhone X'),
                     ('Galaxy 8', 'Galaxy 8'),
                     ('Pixel', 'Pixel'),
                     ('Pixel 2', 'Pixel 2'),
                     ('Pixel XL', 'Pixel XL')]
    model = SelectField('Model',
                        choices=model_choices)
    device_type = RadioField('Device Type',
                             choices=[('phone', 'Phone'), ('tablet', 'Tablet')]
                             )
    os_version = StringField('OS Version')
    office = RadioField('Office Location',
                        choices=[('Omaha', 'Omaha'), ('Lincoln', 'Lincoln')]
                        )
    submit = SubmitField('Add')


class SettingsForm(FlaskForm):
    slack_channel = StringField('Slack Channel')
    slack_team_channel = StringField('Slack Team Channel')
    reminder_interval = StringField('Reminder Interval')
    checkout_length = StringField('Checkout Length')
    office_location = StringField('Office Location')
    message = StringField('Slack Message')
    update_submit = SubmitField('Update')


class UploadFileForm(FlaskForm):
    file = FileField('Choose csv file')
    upload_submit = SubmitField("Upload")
