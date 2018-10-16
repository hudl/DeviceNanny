#!/usr/bin/env python3
#
# The Device Nanny
# Hudl
#
# Created by Ethan Seyl 2016
#

from deviceNanny.slack import NannySlacker
from datetime import datetime, timedelta
import deviceNanny.db_actions as db
from flask import current_app
import configparser
import subprocess
import time
import os
import re


def get_serial(port):
    """
    Tries to retrieve serial number from file.
    :param port: USB port
    :return: Device's serial number or None
    """
    try:
        file = open("/sys/bus/usb/devices/{}/serial".format(port))
        for line in file:
            serial = line.rstrip()
        file.close()
        return serial
    except:
        return None


def usb_devices():
    """
    Get all directory names from /sys/bus/usb/devices/.  Names correspond
    to USB ports/kernels.
    :return: Directory names
    """
    dir_names = next(os.walk('/sys/bus/usb/devices/'))
    return dir_names[1]


def check_usb_connections():
    """
    Iterate through directory names for info.
    """
    connections = usb_devices()
    for c in connections:
        update_db(c)


def update_db(port):
    """
    If the serial number from get_serial(port) is registered in the database
    and the device is checked out, checks the device back in. Keeps database up-to-date
    and accurate in the event the checkout/in process crashes or devices are taken while
    the system is turned off.
    :param port: USB port
    """
    location = 'Test'
    serial = get_serial(port)
    if serial is None:
        was_port_registered(location, port)
    device_id = db.get_device_id_from_serial(serial)
    if device_id:
        if is_device_checked_out(device_id):
            db.check_in(device_id, port)
            NannySlacker.nanny_check_in(db.get_device_name_from_id(device_id))
            current_app.logger.info(
                "[nanny][update_db] Device {} checked in.".format(device_id))
        else:
            current_app.logger.debug("[nanny][update_db] Device {} isn't checked out.".
                          format(device_id))
            verify_match(serial, location, port, device_id)


def was_port_registered(location, port):
    """
    Checks if the device is registered to the correct port in the database. If not, checks
    it out to be fixed on next nanny run.
    :param port: USB port
    """
    device_id = db.get_device_id_from_port(location, port)
    if device_id:
        current_app.logger.debug(
            "[nanny][update_db] Device was registered to a different port. Fixing."
        )
        db.check_out('1', device_id)


def verify_match(serial, location, port, device_id):
    """
    Compare serial number for the port in the database to serial number in the port's directory.
    If the serial number is different, check out that serial and clear the port. Register that
    port to the correct serial in the port's directory.
    :param serial:
    :param port:
    :param device_id:
    :return:
    """
    serial_from_file = serial
    try:
        serial_from_db = db.get_serial_number_from_port(location, port)
    except:
        serial_from_db = None
    current_app.logger.debug("[nanny][verify_match] SN from File: {} SN From DB: {}".
                  format(serial_from_file, serial_from_db))
    if serial_from_file != serial_from_db:
        current_app.logger.debug(
            "[nanny][verify_match] Serial numbers don't match - fixing port {}".
            format(port))
        db.check_out('1', device_id)
        current_app.logger.info(
            "[nanny][verify_match] Nanny checked out device {}. Will be checked in on the next "
            "Nanny run.".format(device_id))
    else:
        current_app.logger.debug("[nanny][verify_match] Serial numbers match for port {}".
                      format(port))


def is_device_checked_out(device_id):
    """
    Checks to see if the device is checked out or missing.
    :param device_id: Device ID
    :return: True or False if checked in or out
    """
    checked_out_by = db.checked_out_by(device_id)
    if checked_out_by is 1:
        current_app.logger.debug(
            "[nanny][is_device_checked_out] Device {} is registered as missing".
            format(device_id))
        return True
    elif checked_out_by is not 0:
        current_app.logger.debug(
            "[nanny][is_device_checked_out] Device {} is checked out by {}".
            format(device_id, checked_out_by))
        return True
    else:
        current_app.logger.debug(
            "[nanny][is_device_checked_out] Device {} is not checked out".
            format(device_id))
        return False


def reminder_due(device_status):
    """
    Finds out if user needs a reminder to check back in a device. If the user needs
    a reminder, make sure it's a weekday between 8-5pm.
    :param device_status: device_name, checked_out_by, time_checked_out, last_reminded, RFID
    :return: True or None depending on if a reminder is needed
    """
    reminder_interval = 100000
    time_since_reminded = int(time.time()) - device_status.get("last_reminded")
    current_app.logger.debug("[nanny][reminder_due] Last reminded {} seconds ago.".format(
        time_since_reminded))
    if time_since_reminded > int(reminder_interval) and checkout_expired(device_status):
        if workday():
            current_app.logger.debug("[nanny][reminder_due] Device needs a reminder")
            return True


def workday():
    """
    Checks to see if it's a weekday between 8-5.
    :return: True or False
    """
    d = datetime.now()
    if d.isoweekday() in range(1, 6) and d.hour in range(8, 17):
        current_app.logger.debug("[nanny][workday] It is during work hours.")
        return True
    else:
        return False


def checkout_expired(device_status):
    """
    Compares current time to the time the device was checked out. If past
    the time set in config file, checkout is expired.
    :param device_status: device_name, checked_out_by, time_checked_out, last_reminded, RFID
    :return: True or None
    """
    checkout_expires = 10000
    if int(time.time()) - device_status.get("time_checked_out") > int(checkout_expires):
        current_app.logger.debug(
            "[nanny][checkout_expired] Checkout expired for device {}".format(
                device_status.get('device_name')))
        return True


def time_since_checkout(device_status):
    """
    Finds the time since device was checked out and converts it to a
    readable format.
    :param device_status: device_name, checked_out_by, time_checked_out, last_reminded, RFID
    :return: Hours and days since device was checked out in human readable format
    """
    sec = timedelta(
        seconds=int(time.time() - device_status.get("time_checked_out")))
    d = datetime(1, 1, 1) + sec
    return "{} days, {} hours".format(d.day - 1, d.hour)


def slack_id(device_status):
    """
    :param device_status: device_name, checked_out_by, time_checked_out, last_reminded, RFID
    :return: Slack ID of user that checked out device
    """
    slack_id = db.get_slack_id(device_status.get("checked_out_by"))
    return slack_id.get("slack_id")


def send_reminder(device_status):
    """
    Sends a reminder slack message to whoever checked out the device if the
    checkout has expired.
    :param device_status: device_name, checked_out_by, time_checked_out, last_reminded, RFID
    """
    if reminder_due(device_status):
        current_app.logger.debug(
            "[nanny][send_reminder] Device checked out by {} type {}".format(
                device_status.get('checked_out_by'),
                type(device_status.get('checked_out_by'))))
        if device_status.get('checked_out_by') is not 1:
            current_app.logger.debug("[nanny][send_reminder] User reminder...")
            NannySlacker.user_reminder(
                slack_id(device_status),
                time_since_checkout(device_status),
                device_status.get("device_name"))
        else:
            NannySlacker.missing_device_message(
                device_status.get('device_name'),
                time_since_checkout(device_status))
        db.update_time_reminded(device_status.get("device_name"))


def checkout_reminders():
    """
    Checks every device in the database to see if it's checked out.
    """
    location = 'Test'
    device_ids = db.device_ids()
    devices = []
    for x in device_ids:
        devices.append(x['device_id'])
    for x in devices:
        current_app.logger.debug("DEVICE: {}".format(x))
        device_status = db.get_device_status(x)
        current_app.logger.debug("DEVICE STATUS: {}".format(device_status))
        if device_status["checked_out_by"] is not 0 and device_status["location"] == location:
            print(
                "CHECKED OUT BY: {}".format(device_status.get("checked_out_by")))
            print("DEVICE location: {}".format(device_status.get("location")))
            current_app.logger.debug(
                "[nanny][checkout_reminders] Check if device {} needs a reminder.".
                format(x))
            print("NEEDS REMINDER")
            send_reminder(device_status)
        else:
            print("NONONONONO")


def registered_ports(location):
    """
    Gets all the ports registered in the database. If a device has a registered
    port, it's connected to the Pi.
    :return: Every port registered in database.
    """
    ports = db.get_registered_ports(location)
    current_app.logger.debug("portS: {}".format(ports))
    values = []
    for i in ports:
        values.append(i['port'])
    return values


def missing_devices():
    """
    Compares the list of all registered ports to the ports that have devices connected.
    :return: List of ports that are registered but are no longer in use (device is gone)
    """
    return set(registered_ports('Test')) - set(usb_devices())


def missing_device_ids(missing_devices):
    """
    Gets the device ID for the devices that are registered to a port but are
    no longer connected.
    :param missing_devices: List of ports that are registered but are no longer in use (device is gone)
    :return: The missing device's device IDs
    """
    location = 'Test'
    return [
        db.get_device_id_from_port(location, port) for port in missing_devices
    ]


def verify_registered_connections():
    """
    Iterates through list of missing devices and checks each of them out.
    '1' is the user Missing Device in the Users database. This keeps the database
    up-to-date even if devices are taken when the checkout system has crashed
    or is turned off.
    """
    checked_out = missing_device_ids(missing_devices())
    for device in checked_out:
        db.check_out('1', device)
        current_app.logger.debug(
            "[nanny][verify_registered_connections] Device {} not connected. Checked out.".
            format(device))


def is_checkout_running():
    """
    Checks to see if a checkout is in progress.
    :return: True or False
    """
    # if glob.glob('/tmp/*.nanny'):
    #     current_app.logger.info("[nanny][is_checkout_running] Checkout is running. Skip.")
    #     return True
    # current_app.logger.debug("[nanny][is_checkout_running] Checkout not running.")
    return False


def clean_tmp_file():
    """
    Removes any .nanny files created by the checkout system. This will allow a device to be
    checked in/out on a port that may have had an issue where the temp file wasn't removed.
    """
    for f in os.listdir('/tmp'):
        if re.search('.nanny', f):
            os.remove(os.path.join('/tmp', f))
