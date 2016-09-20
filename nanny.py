#!/usr/bin/env python3
#
# The Device Nanny
# Hudl
#
# Created by Ethan Seyl 2016
#

from datetime import datetime, timedelta
from db_actions import MyDB
import logging.config
from os import walk
import configparser
import subprocess
import logging
import slack
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
    dir_names = next(walk('/sys/bus/usb/devices/'))
    return dir_names[1]


def check_usb_connections():
    """
    Iterate through directory names for info.
    """
    connections = usb_devices()
    for c in connections:
        print("Checking port {}".format(c))
        update_db(c)


def update_db(port):
    """
    If the serial number from get_serial(port) is registered in the database
    and the device is checked out, checks the device back in. Keeps database up-to-date
    and accurate in the event the checkout/in process crashes or devices are taken while
    the system is turned off.
    :param port: USB port
    """
    serial = get_serial(port)
    if serial is None:
        was_port_registered(port)
    device_id = db.get_device_id_from_serial(serial)
    if device_id:
        if is_device_checked_out(device_id):
            db.check_in(device_id, port)
            slack.nanny_check_in(db.get_device_name_from_id(device_id))
            logging.info("[nanny][update_db] Device {} checked in.".format(
                device_id))
        else:
            logging.debug(
                "[nanny][update_db] Device {} isn't checked out.".format(
                    device_id))
            verify_match(serial, port, device_id)


def was_port_registered(port):
    """
    Checks if the device is registered to the correct port in the database. If not, checks
    it out to be fixed on next nanny run.
    :param port: USB port
    """
    device_id = db.get_device_id_from_port(port)
    if device_id:
        logging.debug(
            "[nanny][update_db] Device was registered to a different port. Fixing.")
        db.check_out('1', device_id)


def verify_match(serial, port, device_id):
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
        serial_from_db = db.get_serial_number_from_port(port)
    except:
        serial_from_db = None
    logging.debug(
        "[nanny][verify_match] SN from File: {} SN From DB: {}".format(
            serial_from_file, serial_from_db))
    if serial_from_file != serial_from_db:
        logging.debug(
            "[nanny][verify_match] Serial numbers don't match - fixing port {}".format(
                port))
        db.check_out('1', device_id)
        logging.info(
            "[nanny][verify_match] Nanny checked out device {}. Will be checked in on the next "
            "Nanny run.".format(device_id))
    else:
        logging.debug(
            "[nanny][verify_match] Serial numbers match for port {}".format(
                port))


def is_device_checked_out(device_id):
    """
    Checks to see if the device is checked out or missing.
    :param device_id: Device ID
    :return: True or False if checked in or out
    """
    checked_out_by = db.checked_out_by(device_id)
    if checked_out_by is 1:
        logging.debug(
            "[nanny][is_device_checked_out] Device {} is registered as missing".format(
                device_id))
        return True
    elif checked_out_by is not 0:
        logging.debug(
            "[nanny][is_device_checked_out] Device {} is checked out by {}".format(
                device_id, checked_out_by))
        return True
    else:
        logging.debug(
            "[nanny][is_device_checked_out] Device {} is not checked out".format(
                device_id))
        return False


def reminder_due(device_status):
    """
    Finds out if user needs a reminder to check back in a device. If the user needs
    a reminder, make sure it's a weekday between 8-5pm.
    :param device_status: DeviceName, CheckedOutBy, TimeCheckedOut, LastReminded, RFID
    :return: True or None depending on if a reminder is needed
    """
    time_since_reminded = int(time.time()) - device_status.get("LastReminded")
    logging.debug("[nanny][reminder_due] Last reminded {} seconds ago.".format(
        time_since_reminded))
    if time_since_reminded > int(config['DEFAULT'][
            'ReminderInterval']) and checkout_expired(device_status):
        if workday():
            logging.debug("[nanny][reminder_due] Device needs a reminder")
            return True


def workday():
    """
    Checks to see if it's a weekday between 8-5.
    :return: True or False
    """
    d = datetime.now()
    if d.isoweekday() in range(1, 6) and d.hour in range(8, 17):
        logging.debug("[nanny][workday] It is during work hours.")
        return True
    else:
        return False


def checkout_expired(device_status):
    """
    Compares current time to the time the device was checked out. If past
    the time set in config file, checkout is expired.
    :param device_status: DeviceName, CheckedOutBy, TimeCheckedOut, LastReminded, RFID
    :return: True or None
    """
    if int(time.time()) - device_status.get("TimeCheckedOut") > int(config[
            'DEFAULT']['CheckoutExpires']):
        logging.debug(
            "[nanny][checkout_expired] Checkout expired for device {}".format(
                device_status.get('DeviceName')))
        return True


def time_since_checkout(device_status):
    """
    Finds the time since device was checked out and converts it to a
    readable format.
    :param device_status: DeviceName, CheckedOutBy, TimeCheckedOut, LastReminded, RFID
    :return: Hours and days since device was checked out in human readable format
    """
    sec = timedelta(
        seconds=int(time.time() - device_status.get("TimeCheckedOut")))
    d = datetime(1, 1, 1) + sec
    return "{} days, {} hours".format(d.day - 1, d.hour)


def slack_id(device_status):
    """
    :param device_status: DeviceName, CheckedOutBy, TimeCheckedOut, LastReminded, RFID
    :return: Slack ID of user that checked out device
    """
    slack_id = db.get_slack_id(device_status.get("CheckedOutBy"))
    return slack_id.get("SlackID")


def send_reminder(device_status):
    """
    Sends a reminder slack message to whoever checked out the device if the
    checkout has expired.
    :param device_status: DeviceName, CheckedOutBy, TimeCheckedOut, LastReminded, RFID
    """
    if reminder_due(device_status):
        logging.debug(
            "[nanny][send_reminder] Device checked out by {} type {}".format(
                device_status.get('CheckedOutBy'), type(device_status.get(
                    'CheckedOutBy'))))
        if device_status.get('CheckedOutBy') is not 1:
            logging.debug("[nanny][send_reminder] User reminder...")
            slack.user_reminder(
                slack_id(device_status), time_since_checkout(device_status),
                device_status.get("DeviceName"))
        else:
            slack.missing_device_message(
                device_status.get('DeviceName'),
                time_since_checkout(device_status))
        db.update_time_reminded(device_status.get("DeviceName"))


def checkout_reminders():
    """
    Checks every device in the database to see if it's checked out.
    """
    device_ids = db.device_ids()
    devices = []
    for x in device_ids:
        devices += x.values()
    print(devices)
    for x in devices:
        device_status = db.get_device_status(x)
        if device_status.get("CheckedOutBy") is not 0:
            logging.debug(
                "[nanny][checkout_reminders] Check if device {} needs a reminder.".format(
                    x))
            send_reminder(device_status)


def registered_ports():
    """
    Gets all the ports registered in the database. If a device has a registered
    port, it's connected to the Pi.
    :return: Every port registered in database.
    """
    ports = db.get_registered_ports()
    values = []
    for i in ports:
        values += i.values()
    return values


def missing_devices():
    """
    Compares the list of all registered ports to the ports that have devices connected.
    :return: List of ports that are registered but are no longer in use (device is gone)
    """
    return set(registered_ports()) - set(usb_devices())


def missing_device_ids(missing_devices):
    """
    Gets the device ID for the devices that are registered to a port but are
    no longer connected.
    :param missing_devices: List of ports that are registered but are no longer in use (device is gone)
    :return: The missing device's device IDs
    """
    device_ids = [db.get_device_id_from_port(x) for x in missing_devices]
    return device_ids


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
        logging.debug(
            "[nanny][verify_registered_connections] Device {} not connected. Checked out.".format(
                device))


def is_checkout_running():
    """
    Checks to see if a USB action is happening by looking for the process ID
    of the shell script called by UDEV.
    :return: True or False
    """
    proc = subprocess.Popen(["pgrep -f [s]tart_usb_checkout"],
                            stdout=subprocess.PIPE,
                            shell=True)
    (out, err) = proc.communicate()
    pid = (out.decode('utf-8')).splitlines()
    if pid:
        logging.info("[nanny][is_checkout_running] Checkout is running. Skip.")
        return True
    logging.debug("[nanny][is_checkout_running] Checkout not running.")
    return False


def clean_tmp_file():
    """
    Removes any .nanny files created by the checkout system. This will allow a device to be
    checked in/out on a port that may have had an issue where the temp file wasn't removed.
    """
    for f in os.listdir('/tmp'):
        if re.search('.nanny', f):
            os.remove(os.path.join('/tmp', f))


def main():
    """
    Keeps the database up-to-date by looking for devices that have been attached/removed
    from the Pi without checking them in/out, then sends a reminder to users who
    have expired checkouts.
    :return:
    """
    if is_checkout_running() is False:
        clean_tmp_file()
        check_usb_connections()
        verify_registered_connections()
        checkout_reminders()


if __name__ == "__main__":
    logging.config.fileConfig("config/nanny_logging.conf")
    config = configparser.ConfigParser()
    config.read('config/DeviceNanny.ini')
    logging.info("[nanny] Started")
    global db
    db = MyDB()
    main()
    logging.info("[nanny] Finished")
