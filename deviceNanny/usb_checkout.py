#!/usr/bin/env python3
#
# USB Checkout
# Hudl
#
# Created by Ethan Seyl 2016
#

import multiprocessing
import logging.config
import configparser
import subprocess
import logging
import socket
import slack
import time
import sys
import os
import re


def get_lock(process_name):
    """
    Prevents start_usb_checkout from starting after
    another USB action takes place on the same port
    before checkout is completed.
    """
    get_lock._lock_socket = socket.socket(socket.AF_UNIX, socket.SOCK_DGRAM)

    try:
        get_lock._lock_socket.bind('\0' + process_name)
        logging.warning(
            "[usb_checkout][get_lock] Prevented process from starting - already running."
        )
        popups('USB Connection')
    except socket.error:
        logging.warning("[usb_checkout][get_lock] Process already locked.")


def create_tempfile(port):
    """
    Creates a file with the name of the kernel in tmp directory
    :param port: Kernel of the USB port
    :return filename: /tmp/*kernel*.nanny
    """
    filename = '/tmp/{}.nanny'.format(port)
    check_for_tempfile(filename)
    with open(filename, 'w+b'):
        return filename


def delete_tempfile(filename):
    """
    Deletes the file created in create_tempfile().
    :param filename: /tmp/*kernel*.nanny
    """
    try:
        os.remove(filename)
        logging.debug("[usb_checkout][delete_tempfile] Temp file deleted.")
    except IOError as e:
        logging.debug(
            "[usb_checkout][delete_tempfile] Temp file doesn't exist. {}".
            format(str(e)))


def check_for_tempfile(filename):
    """
    Checks the /tmp directory for a file matching the kernel name
    and ending in .nanny. If found, alerts user and exits.
    :param filename: /tmp/*kernel*.nanny
    """
    if os.path.isfile(filename):
        get_lock('usb_checkout')
        sys.exit()


def cancelled():
    """
    Called if user cancels checkout. If a user didn't plug the device back in before cancelling
    it will be checked out as missing. Also, if multiple devices were taken, cancelling one
    won't close all checkout processes.
    """
    if not is_device_connected(port):
        db.check_out('1', device_id)
        slack.help_message(device_name)
    if multiple_checkouts():
        delete_tempfile(filename)
        logging.debug("[usb_checkout][cancelled] FINISHED")
    else:
        stop_program_if_running()


def is_device_connected(port):
    """
    Checks to see if the device is still connected if a user cancels checkout.
    :param port: USB port
    :return: True or False
    """
    try:
        open("/sys/bus/usb/devices/{}/serial".format(port))
        logging.info(
            "[usb_checkout][is_device_connected] Checkout cancelled - device still connected"
        )
        return True
    except:
        return False


def multiple_checkouts():
    """
    Checks to see if multiple devices were unplugged before user info was submitted.
    :return: True or None
    """
    pid = get_pid("[s]tart_checkout")
    if len(pid) > 1:
        logging.debug(
            "[usb_checkout][multiple_checkouts] Multiple checkouts in progress."
        )
        return True


def timeout(x):
    """
    30 second timer started during checkout. If user doesn't enter info
    before timeout ends, calls cancelled().
    :param x: 30
    """
    time.sleep(x)
    logging.warning("[usb_checkout][timeout] TIMEOUT")
    cancelled()


def stop_program_if_running():
    """
    Gets the group process ID from the process ID of shell script triggered by UDEV rule.
    Then calls the kill function.
    """
    pid = get_pid("[s]tart_checkout")
    print(pid)
    print(type(pid))
    pgid = os.getpgid(int(pid[0]))
    logging.debug(
        "[usb_checkout][stop_program_if_running] PGID: {}".format(pgid))
    delete_tempfile(filename)
    kill(pgid)


def get_pid(string):
    """
    :param string: [s]tart_checkout
    :return: process ID(s) as int
    """
    pid = (subprocess.check_output(
        ['pgrep', '-f', '{}'.format(string)])).decode('utf-8').splitlines()
    logging.debug("[usb_checkout][get_pid] PID(s): {}".format(pid))
    return pid


def kill(pgid):
    """
    Kills group process ID.
    :param pgid: Group process ID
    """
    logging.debug("[usb_checkout][kill] FINISHED")
    os.system('pkill -9 -g {}'.format(pgid))


def dialog(popup):
    """
    Displays Zenity window.
    :param popup: Parameters set in popups()
    :return: user input from window, if needed
    """
    output = subprocess.check_output(popup, timeout=120)
    return output


def return_log():
    """
    :return: The end of the kern.log file
    """
    fname = "/var/log/kern.log"
    with open(fname, 'r') as f:
        f.seek(0, 2)
        fsize = f.tell()
        f.seek(max(fsize - 2000, 0, 0))
        log = f.readlines()
    logging.debug(
        "[usb_checkout][return_log] End of kern.log file: {}".format(log))
    return log


def find_port():
    """
    Searches through the last 200 lines of kern.log for the USB port.
    :return: USB port
    """
    lines = return_log()
    match = "[0-9]-[^:]+"
    matches = [x for x in lines if re.search(match, x)]
    try:
        port = re.search(match, matches[len(matches) - 1]).group().split(" ")
        logging.debug(
            "[usb_checkout][find_port] USB Port from kern.log file: {}".format(
                port[0]))
        return port[0]
    except:
        logging.error(
            "[usb_checkout][find_port] No USB actions found near the end of the log!"
        )
        stop_program_if_running()


def get_serial(port):
    """
    Opens file with the serial number for the USB port.
    :param port: USB port
    :return: Serial number for USB device
    """
    try:
        with open("/sys/bus/usb/devices/{}/serial".format(port)) as f:
            for line in f:
                serial = line.rstrip()
        logging.debug("[usb_checkout][get_serial] Serial number of device: {}".
                      format(serial))
        return serial
    except:
        logging.debug("[usb_checkout][get_serial] Serial number not found.")


def get_user_info():
    """
    Asks user for their name or ID number, and retrieves full info
    from the database.
    :return: FirstName, LastName, SlackID, Office
    """
    try:
        user_input = popups('checkout').decode('utf-8')
        timer.terminate()
        return get_info_from_db(user_input.rstrip('\n').split(' '))
    except Exception as e:
        logging.debug("[usb_checkout][get_user_info] {}".format(str(e)))
        logging.debug(
            "[usb_checkout][get_user_info] User cancelled name entry")
        timer.terminate()
        cancelled()


def get_user_info_from_db(device_id):
    """
    Retrieves user info from the database by device number.
    :param device_id: Device ID number
    :return: FirstName, LastName, SlackID, Office
    """
    checked_out_by = []
    checked_out_by.append(db.checked_out_by(device_id))
    logging.debug(
        "[usb_checkout][get_user_info_from_db] checked_out_by = {}. Type = {}".
        format(checked_out_by, type(checked_out_by)))
    user_info = db.user_info(checked_out_by)
    logging.debug("[usb_checkout][get_user_info_from_db] user_info = {}".
                  format(user_info))
    return user_info


def get_info_from_db(user_input):
    """
    Gets user info from database via input from the user. Checks for
    valid entry.
    :param user_input: Either first and last name or user ID.
    :return: FirstName, LastName, SlackID, Office
    """
    user_info = db.user_info(user_input)
    if (user_info is None) or (user_info.get('FirstName') == '-') or (
            user_info.get('FirstName') == 'Missing'):
        popups('Name Error')
        logging.warning(
            "[usb_checkout][get_info_from_db] {} is not a valid ID or name".
            format(user_input))
        return get_user_info()
    else:
        logging.debug(
            "[usb_checkout][get_info_from_db] User {} checking out device {}".
            format(user_info, device_name))
        return user_info


def popups(msg):
    """
    Various Zenity windows for name errors, checkouts, USB connection issues,
    and new device registers.
    :param msg: Type of message needed
    :return: User input if applicable
    """
    if msg == 'Name Error':
        text = "Not a valid name or ID"
        name_cmd = [
            "zenity", "--error", "--title='ERROR'", "--text='{}'".format(text)
        ]
        dialog(name_cmd)
    elif msg == 'checkout':
        text = "Enter your first and last name OR your user ID number:"
        checkout_cmd = [
            "zenity", "--entry",
            "--title='Device Checkout: {}'".format(device_name),
            "--text='{}'".format(text)
        ]
        return dialog(checkout_cmd)
    elif msg == 'USB Connection':
        text = "Device {} detected more than once. Either you plugged " \
            "it back in without finishing checkout OR it's a bad USB cord.".format(device_name)
        conn_cmd = [
            "zenity", "--error", "--title='ERROR'", "--text='{}'".format(text)
        ]
        dialog(conn_cmd)
    elif msg == 'New Device':
        text = "Add device to database."
        new_cmd = [
            "zenity", "--forms", "--title='New Device'",
            "--text='{}'".format(text),
            "--add-entry='Device Name ex: iPhone 001'",
            "--add-entry='Manufacturer ex: Samsung'",
            "--add-entry='Model ex: iPad Air 2 Black'",
            "--add-entry='Type (Tablet or Phone)'",
            "--add-entry='OS ex: Android 6'"
        ]
        return dialog(new_cmd)


def get_new_device_info(serial):
    """
    Popup window asking user for new device info.
    :return: Device info from user
    """
    try:
        logging.info(
            "[usb_checkout][get_new_device_info] New device. Serial: {}".
            format(serial))
        return popups('New Device').decode('utf-8').split('|')
    except:
        logging.info(
            "[usb_checkout][get_new_device_info] User cancelled new device entry."
        )
        delete_tempfile(filename)
        sys.exit()


def to_database(serial):
    """
    Combines device info provided by user with USB port and serial number.
    """
    device_info = get_new_device_info(serial)
    new_device_id = db.new_device_id()
    device_info.extend([location, new_device_id, get_serial(port), port])
    db.add_to_database(device_info)
    logging.info(
        "[usb_checkout][to_database] Device added: {}".format(device_info))


def check_if_out(location, port):
    """
    Checks to see if the port is registered for a device in the database.
    :param port: USB port
    :return: True or None
    """
    device_id = db.get_device_id_from_port(location, port)
    if device_id is None:
        logging.debug(
            "[usb_checkout][check_if_out] Port {} is not registered to a device.".
            format(port))
        return True


def check_in(device_id, port):
    """
    Checks a device into the database
    :param device_id: Device ID number
    :param port: USB port
    """
    db.check_in(device_id, port)


def check_out(user_info, device_id):
    """
    Checks device out from the database.
    :param user_info: First Name, Last Name, SlackID, Office
    :param device_id: Device ID number
    """
    db.check_out(user_info.get('UserID'), device_id)


def play_sound():
    """
    Plays a beep sound.
    """
    os.system('play --no-show-progress --null --channels 1 synth %s sine %f' %
              (.75, 3000))


def get_device_name(device_id, location, port):
    """
    Tries to get the device name from the port and device ID.
    :param device_id: Device ID
    :param port: USB Port
    :return: Device Name
    """
    device_name = db.get_device_name(location, port)
    if device_name is None:
        logging.debug(
            "[usb_checkout][get_device_name] Unable to get device name from port - trying ID."
        )
        device_name = db.get_device_name_from_id(location, device_id)
    return device_name


def main():
    """
    Assigns variables, checks if device is new or needs checked out/in.
    """
    global location
    location = config['DEFAULT']['Location']
    logging.info("LOCATION: {}".format(location))
    global port
    port = find_port()
    serial = get_serial(port)
    global device_id
    device_id = db.get_device_id_from_serial(serial)
    global device_name
    device_name = get_device_name(device_id, location, port)
    global filename
    filename = create_tempfile(port)
    play_sound()
    if device_id is None and serial is not None:
        to_database(serial)
    else:
        checked_out = check_if_out(location, port)
        if checked_out:
            logging.info("[usb_checkout][main] CHECK IN")
            device_name = db.get_device_name_from_id(location, device_id)
            user_info = get_user_info_from_db(device_id)
            check_in(device_id, port)
            slack.check_in_notice(user_info, device_name)
        else:
            logging.info("[usb_checkout][main] CHECK OUT")
            device_id = db.get_device_id_from_port(location, port)
            device_name = db.get_device_name_from_id(location, device_id)
            timer.start()
            user_info = get_user_info()
            check_out(user_info, device_id)
            slack.check_out_notice(user_info, device_name)
            logging.info(
                "[usb_checkout][main] {} checked out by {} {}.".format(
                    device_name,
                    user_info.get('FirstName'), user_info.get('LastName')))
    delete_tempfile(filename)


if __name__ == "__main__":
    global working_dir
    working_dir = os.path.dirname(__file__)
    config = configparser.ConfigParser()
    config.read('{}/config/DeviceNanny.ini'.format(working_dir))
    logging.config.fileConfig('{}/config/usb_logging.conf'.format(working_dir))
    logging.debug("[usb_checkout] STARTED")
    timer = multiprocessing.Process(target=timeout, name="Timer", args=(30, ))
    main()
    logging.info("[usb_checkout] FINISHED")
