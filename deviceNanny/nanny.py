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
    serial = None
    try:
        file = open("/sys/bus/usb/devices/{}/serial".format(port))
        for line in file:
            serial = line.rstrip()
        file.close()
    except Exception as e:
        current_app.logger.debug('[get_serial] No serial in /usb/devices/{} - {}'.format(port, e))
    return serial


def usb_devices():
    """
    Get all directory names from /sys/bus/usb/devices/.  Names correspond
    to USB ports/kernels.
    :return: Directory names
    """
    dir_names = next(os.walk('/sys/bus/usb/devices/'))
    current_app.logger.debug('[usb_devices] Directory names returned: {}'.format(dir_names[1]))
    return dir_names[1]


def check_usb_connections():
    """
    Iterate through directory names for info.
    """
    connections = usb_devices()
    for c in connections:
        current_app.logger.debug('[check_usb_connections] Connection = {}'.format(c))
        update_db(c)


def update_db(port):
    """
    If the serial number from get_serial(port) is registered in the database
    and the device is checked out, checks the device back in. Keeps database up-to-date
    and accurate in the event the checkout/in process crashes or devices are taken while
    the system is turned off.
    :param port: USB port
    """
    location = current_app.config['location']
    nanny = NannySlacker()
    serial = get_serial(port)
    if serial is None:
        was_port_registered(location, port)
    device_id = db.get_device_id_from_serial(serial)
    if device_id:
        if is_device_checked_out(device_id):
            db.check_in(device_id, port)
            nanny.nanny_check_in(db.get_device_name_from_id(device_id))
            current_app.logger.info(
                "[update_db] Device {} checked in.".format(device_id))
        else:
            current_app.logger.debug("[update_db] Device {} isn't checked out.".format(device_id))
            verify_match(serial, location, port, device_id)


def was_port_registered(location, port):
    """
    Checks if the device is registered to the correct port in the database. If not, checks
    it out to be fixed on next nanny run.
    :param port: USB port
    :param location: Office location
    """
    device_id = db.get_device_id_from_port(location, port)
    if device_id:
        current_app.logger.info("[update_db] Device was registered to a different port. Marking as missing "
                                "so it will be fixed in the next nanny run.")
        db.check_out('2', device_id)


def verify_match(serial, location, port, device_id):
    """
    Compare serial number for the port in the database to serial number in the port's directory.
    If the serial number is different, check out that serial and clear the port. Register that
    port to the correct serial in the port's directory.
    :param serial:
    :param port:
    :param device_id:
    :param location:
    :return:
    """
    serial_from_file = serial
    serial_from_db = db.get_serial_number_from_port(location, port)
    current_app.logger.debug("[verify_match] SN from File: {} SN From DB: {}".
                             format(serial_from_file, serial_from_db))
    if serial_from_file != serial_from_db:
        current_app.logger.debug(
            "[verify_match] Serial numbers don't match - fixing port {}".
            format(port))
        db.check_out(2, device_id)
        current_app.logger.info(
            "[verify_match] Nanny checked out device {}. Will be checked in on the next "
            "Nanny run.".format(device_id))
    else:
        current_app.logger.debug("[verify_match] Serial numbers match for port {}".format(port))


def is_device_checked_out(device_id):
    """
    Checks to see if the device is checked out or missing.
    :param device_id: Device ID
    :return: True or False if checked in or out
    """
    checked_out_by = db.checked_out_by(device_id)
    if checked_out_by is 2:
        current_app.logger.info(
            "[is_device_checked_out] Device {} is registered as missing".
            format(device_id))
        return True
    elif checked_out_by is not 1:
        current_app.logger.info(
            "[is_device_checked_out] Device {} is checked out by {}".
            format(device_id, checked_out_by))
        return True
    else:
        current_app.logger.info(
            "[is_device_checked_out] Device {} is not checked out".
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
    time_since_reminded = int(time.time()) - device_status["last_reminded"]
    current_app.logger.debug("[reminder_due] Last reminded {} seconds ago.".format(time_since_reminded))

    if time_since_reminded > int(reminder_interval) and checkout_expired(device_status) and workday():
        current_app.logger.debug("[reminder_due] Device needs a reminder")
        return True


def workday():
    """
    Checks to see if it's a weekday between 8-5.
    :return: True or False
    """
    d = datetime.now()
    if d.isoweekday() in range(1, 6) and d.hour in range(8, 17):
        current_app.logger.debug("[workday] It is during work hours.")
        return True


def checkout_expired(device_status):
    """
    Compares current time to the time the device was checked out. If past
    the time set in config file, checkout is expired.
    :param device_status: device_name, checked_out_by, time_checked_out, last_reminded, RFID
    :return: True or None
    """
    checkout_expires = 10000
    if int(time.time()) - device_status["time_checked_out"] > int(checkout_expires):
        current_app.logger.debug("[checkout_expired] Checkout expired for device {}"
                                 .format(device_status['device_name']))
        return True


def time_since_checkout(time_since_checked_out):
    """
    Finds the time since device was checked out and converts it to a readable format.
    :param time_since_checked_out: device_name, checked_out_by, time_checked_out, last_reminded, RFID
    :return: Hours and days since device was checked out in human readable format
    """
    sec = timedelta(seconds=int(time.time() - time_since_checked_out))
    d = datetime(1, 1, 1) + sec
    return "{} days, {} hours".format(d.day - 1, d.hour)


def slack_id(checked_out_by):
    """
    :param checked_out_by: device_name, checked_out_by, time_checked_out, last_reminded, RFID
    :return: Slack ID of user that checked out device
    """
    slack_id = db.get_slack_id(checked_out_by)
    return slack_id["slack_id"]


def send_reminder(device_status):
    """
    Sends a reminder slack message to whoever checked out the device if the
    checkout has expired.
    :param device_status: device_name, checked_out_by, time_checked_out, last_reminded, RFID
    """
    if reminder_due(device_status):
        nanny_slacker = NannySlacker()
        if device_status['checked_out_by'] is not 2:
            current_app.logger.info("[send_reminder] Send user a reminder.")
            nanny_slacker.user_reminder(
                slack_id(device_status['checked_out_by']),
                time_since_checkout(device_status['time_since_checked_out']),
                device_status["device_name"])
        else:
            current_app.logger.info("[send_reminder] Post missing device message.")
            nanny_slacker.missing_device_message(device_status['device_name'],
                                                 time_since_checkout(device_status['time_since_checked_out']))
        db.update_time_reminded(device_status["device_name"])


def checkout_reminders():
    """
    Checks every device in the database to see if it's checked out.
    """
    location = current_app.config['location']
    device_ids = db.device_ids()
    devices = []
    for x in device_ids:
        devices.append(x['device_id'])
    for x in devices:
        current_app.logger.debug("[checkout_reminders] DEVICE: {}".format(x))
        device_status = db.get_device_status(x)
        if device_status["checked_out_by"] is not 1 and device_status["location"] == location:
            current_app.logger.debug("[checkout_reminders] CHECKED OUT BY: {}"
                                     .format(device_status["checked_out_by"]))
            current_app.logger.debug("[checkout_reminders] Check if device {} needs a reminder.".format(x))
            send_reminder(device_status)
        else:
            current_app.logger.debug('[checkout_reminders] No reminder needed for device')


def registered_ports():
    """
    Gets all the ports registered in the database. If a device has a registered
    port, it's connected to the Pi.
    :return: Every port registered in database.
    """
    location = current_app.config['location']
    ports = db.get_registered_ports(location)
    current_app.logger.debug("[registered_ports] ports: {}".format(ports))
    values = []
    for i in ports:
        values.append(i['port'])
    current_app.logger.debug("[registered_ports] VALUES: {}".format(values))
    return values


def missing_devices():
    """
    Compares the list of all registered ports to the ports that have devices connected.
    :return: List of ports that are registered but are no longer in use (device is gone)
    """
    ports = set(registered_ports()) - set(usb_devices())
    current_app.logger.debug('[missing_devices] Ports: {} Type: {}'.format(ports, type(ports)))
    return ports


def missing_device_ids(missing_devices):
    """
    Gets the device ID for the devices that are registered to a port but are
    no longer connected.
    :param missing_devices: List of ports that are registered but are no longer in use (device is gone)
    :return: The missing device's device IDs
    """
    location = current_app.config['location']
    current_app.logger.debug('[missing_device_ids] Missing device ports: {}'.format(missing_devices))
    missing_ids = [db.get_device_id_from_port(location, port) for port in missing_devices]
    current_app.logger.debug('[missing_device_ids] Missing device IDs: {}'.format(missing_ids))
    return missing_ids


def verify_registered_connections():
    """
    Iterates through list of missing devices and checks each of them out.
    '2' is the user Missing Device in the Users database. This keeps the database
    up-to-date even if devices are taken when the checkout system has crashed
    or is turned off.
    """
    checked_out = missing_device_ids(missing_devices())
    for device in checked_out:
        current_app.logger.debug(
            "[verify_registered_connections] Device {} not connected. Checked it out.".format(device))
        db.check_out(2, device)


def is_checkout_running():
    """
    Checks to see if a checkout is in progress.
    :return: True or False
    """
    # if glob.glob('/tmp/*.nanny'):
    #     current_app.logger.info("[is_checkout_running] Checkout is running. Skip.")
    #     return True
    # current_app.logger.debug("[is_checkout_running] Checkout not running.")
    return False


def clean_tmp_file():
    """
    Removes any .nanny files created by the checkout system. This will allow a device to be
    checked in/out on a port that may have had an issue where the temp file wasn't removed.
    """
    for f in os.listdir('/tmp'):
        if re.search('.nanny', f):
            os.remove(os.path.join('/tmp', f))
