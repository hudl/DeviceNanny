#!/usr/bin/env python3
#
# USB Checkout
# Hudl
#
# Created by Ethan Seyl 2016
#

from deviceNanny.slack import NannySlacker
import deviceNanny.db_actions as db
from flask import current_app
import subprocess
import time
import os
import re


def get_lock(process_name, device_name):
    # """
    # Prevents start_usb_checkout from starting after
    # another USB action takes place on the same port
    # before checkout is completed.
    # """
    # get_lock._lock_socket = socket.socket(socket.AF_UNIX, socket.SOCK_DGRAM)
    #
    # try:
    #     get_lock._lock_socket.bind('\0' + process_name)
    #     current_app.logger.warn(
    #         "[usb_checkout][get_lock] Prevented process from starting - already running."
    #     )
    #     popups('USB Connection', device_name)
    # except socket.error:
    #     current_app.logger.warn("[usb_checkout][get_lock] Process already locked.")
    pass


def create_tempfile(port, device_name):
    """
    Creates a file with the name of the kernel in tmp directory
    :param port: Kernel of the USB port
    :return filename: /tmp/*kernel*.nanny
    """
    filename = '/tmp/{}.nanny'.format(port)
    if check_for_tempfile(filename, device_name):
        return
    with open(filename, 'w+b'):
        return filename


def delete_tempfile(filename):
    """
    Deletes the file created in create_tempfile().
    :param filename: /tmp/*kernel*.nanny
    """
    try:
        os.remove(filename)
        current_app.logger.debug("[usb_checkout][delete_tempfile] Temp file deleted.")
    except IOError as e:
        current_app.logger.debug(
            "[usb_checkout][delete_tempfile] Temp file doesn't exist. {}".
            format(str(e)))


def check_for_tempfile(filename, device_name):
    """
    Checks the /tmp directory for a file matching the kernel name
    and ending in .nanny. If found, alerts user and exits.
    :param filename: /tmp/*kernel*.nanny
    """
    if os.path.isfile(filename):
        get_lock('usb_checkout', device_name)
        return True


def cancelled(port, device_name, filename):
    """
    Called if user cancels checkout. If a user didn't plug the device back in before cancelling
    it will be checked out as missing. Also, if multiple devices were taken, cancelling one
    won't close all checkout processes.
    """
    nanny = NannySlacker()
    if not is_device_connected(port):
        nanny.help_message(device_name)
    if multiple_checkouts():
        delete_tempfile(filename)
        current_app.logger.debug("[cancelled] FINISHED")


def is_device_connected(port):
    """
    Checks to see if the device is still connected if a user cancels checkout.
    :param port: USB port
    :return: True or False
    """
    try:
        open("/sys/bus/usb/devices/{}/serial".format(port))
        current_app.logger.info(
            "[is_device_connected] Checkout cancelled - device still connected"
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
        current_app.logger.debug(
            "[multiple_checkouts] Multiple checkouts in progress."
        )
        return True
    else:
        current_app.logger.debug('[multiple_checkouts] One checkout in progress...')


def timeout(x, port, device_id, device_name, filename):
    """
    30 second timer started during checkout. If user doesn't enter info
    before timeout ends, calls cancelled().
    :param x: 30
    """
    time.sleep(x)
    current_app.logger.warn("[timeout] TIMEOUT")


def stop_program_if_running():
    """
    Gets the group process ID from the process ID of shell script triggered by UDEV rule.
    Then calls the kill function.
    """
    pid = get_pid("[s]tart_checkout")
    print(pid)
    print(type(pid))
    pgid = os.getpgid(int(pid[0]))
    current_app.logger.debug(
        "[stop_program_if_running] PGID: {}".format(pgid))
    kill(pgid)


def get_pid(string):
    """
    :param string: [s]tart_checkout
    :return: process ID(s) as int
    """
    pid = (subprocess.Popen(['pgrep', '-f', '{}'.format(string)], stdout=subprocess.PIPE).communicate()[0]).decode("utf-8")
    current_app.logger.debug("[get_pid] pid(s): {}".format(pid))
    pid = pid.splitlines()
    if type(pid) is list:
        return pid
    else:
        return [pid]


def kill(pgid):
    """
    Kills group process ID.
    :param pgid: Group process ID
    """
    current_app.logger.debug("[kill] FINISHED")
    os.system('pkill -9 -g {}'.format(pgid))


def dialog(popup):
    """
    Displays Zenity window.
    :param popup: Parameters set in popups()
    :return: user input from window, if needed
    """
    if '--question' in popup:
        output = os.system(popup)
        current_app.logger.debug('[dialog] Output: {}'.format(output))
    else:
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
    current_app.logger.debug(
        "[return_log] End of kern.log file: {}".format(log))
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
        current_app.logger.debug(
            "[find_port] USB Port from kern.log file: {}".format(
                port[0]))
        return port[0]
    except:
        current_app.logger.error("[find_port] No USB actions found near the end of the log!")


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
        current_app.logger.debug("[get_serial] Serial number of device: {}".format(serial))
        return serial
    except:
        current_app.logger.debug("[get_serial] Serial number not found.")


def get_user_info(timer, port, device_id, device_name, filename):
    """
    Asks user for their name or ID number, and retrieves full info
    from the database.
    :return: FirstName, LastName, SlackID, location
    """
    try:
        user_input = popups('checkout', device_name).decode('utf-8')
        timer.terminate()
        return get_info_from_db(user_input.rstrip('\n').split(' '), timer, port, device_id, device_name, filename)
    except Exception as e:
        current_app.logger.debug("[get_user_info] Maybe user cancelled name entry: {}".format(e))
        timer.terminate()
        cancelled(port, device_name, filename)
        return {'id': 2}


def get_user_info_from_db(device_id):
    """
    Retrieves user info from the database by device number.
    :param device_id: Device ID number
    :return: FirstName, LastName, SlackID, location
    """
    checked_out_by = []
    checked_out_by.append(db.checked_out_by(device_id))
    current_app.logger.debug("[get_user_info_from_db] checked_out_by = {}".format(checked_out_by))
    new_user, user_info = db.user_info(checked_out_by)
    return user_info


def get_info_from_db(user_input, timer, port, device_id, device_name, filename):
    """
    Gets user info from database via input from the user. Checks for
    valid entry.
    :param user_input: Either first and last name or user ID.
    :return: FirstName, LastName, SlackID, location
    """
    new_user, user_info = db.user_info(user_input)
    if (user_info is None) or (user_info['id'] == 1) or (user_info['first_name'] == 'Missing') or new_user:
        current_app.logger.info("[get_info_from_db] {} is not a valid ID or name".format(user_input))
        add_user = popups('Name Error', user_info)
        current_app.logger.info("[get_info_from_db] ADD USER RESPONSE: {}".format(add_user))
        if add_user == 0:
            ignore, user_info = add_new_user_to_db(user_info)
            current_app.logger.debug('[get_info_from_db] User Info: {} {} {} {} {}'.format(user_info['first_name'],
                                                                                           user_info['last_name'],
                                                                                           user_info['id'],
                                                                                           user_info['slack_id'],
                                                                                           user_info['location']))
            return user_info
        else:
            return get_user_info(timer, port, device_id, device_name, filename)
    else:
        current_app.logger.debug("[get_info_from_db] User {} checking out device {}".
                                 format(user_info['id'], device_name))
        return user_info


def add_new_user_to_db(user_info):
    first_name = user_info['first_name']
    last_name = user_info['last_name']
    user_info['slack_id'] = get_slack_id(first_name + ' ' + last_name)
    user_info['location'] = current_app.config['location']
    current_app.logger.debug('[add_new_user_to_db] USER INFO: {}'.format(user_info))
    db.add_user_to_database(user_info)
    user_info = db.user_info([first_name, last_name])
    return user_info


def get_slack_id(name):
    nanny_slacker = NannySlacker()
    try:
        current_app.logger.debug('[get_slack_id] Name: {}'.format(name))
        for user in nanny_slacker.slack.users.list().body['members']:
            if not user['deleted']:
                if user['real_name'] == name:
                    current_app.logger.info('[get_slack_id] Slack ID found: {}'.format(user['id']))
                    return user['id']
        current_app.logger.warn('[get_slack_id] No Slack ID for for {}'.format(name))
    except Exception as e:
        current_app.logger.error('[get_slack_id] Exception: {}'.format(e))


def popups(msg, info):
    """
    Various Zenity windows for name errors, checkouts, USB connection issues,
    and new device registers.
    :param msg: Type of message needed
    :param info: Device name or user input
    :return: User input if applicable
    """
    if msg == 'Name Error':
        text = "Not\ a\ valid\ name\ or\ ID.\ Would\ you\ like\ to\ add\ the\ user\ {}\ {}?".format(info['first_name'], info['last_name'])
        name_cmd = "zenity --question --title Invalid\ Entry --text {} --ok-label Yes --cancel-label No".format(text)
        return dialog(name_cmd)
    elif msg == 'checkout':
        text = "Enter your first and last name OR your user ID number:"
        checkout_cmd = [
            "zenity", "--entry",
            "--title='Device Checkout: {}'".format(info),
            "--text='{}'".format(text)
        ]
        return dialog(checkout_cmd)
    elif msg == 'USB Connection':
        text = "Device {} detected more than once. Either you plugged " \
            "it back in without finishing checkout OR it's a bad USB cord.".format(info)
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
    elif msg == 'Request Device':
        text = "Enter your first and last name or ID number:"
        request_cmd = [
            "zenity", "--entry", "--title='Request Device'", "--text='{}'".format(text)
        ]
        return dialog(request_cmd)


def get_user_info_from_popup(popup_type):
    user_input = popups(popup_type, None).split()
    first_name = user_input.pop(0)
    last_name = ' '.join(user_input)
    full_name = [first_name, last_name]
    current_app.logger.debug('[user_input_from_popup] User Input: {}'.format(user_input))
    try:
        user_info = db.db_fetch("SELECT * from users WHERE first_name = '{}' AND last_name = '{}'"
                                .format(full_name[0], full_name[1]))
        return user_info
    except Exception as e:
        current_app.logger.debug('[get_user_info_from_popup] Exception: {}'.format(e))


def get_new_device_info(serial, filename):
    """
    Popup window asking user for new device info.
    :return: Device info from user
    """
    try:
        current_app.logger.info("[get_new_device_info] New device. Serial: {}".format(serial))
        return popups('New Device', 'None').decode('utf-8').split('|')
    # except Exception as e:
    except subprocess.CalledProcessError as e:
        current_app.logger.info(
            "[get_new_device_info] User cancelled new device entry. Exception: {}".format(e)
        )
        delete_tempfile(filename)


def to_database(serial, port, location, filename):
    """
    Combines device info provided by user with USB port and serial number.
    """
    device_info = get_new_device_info(serial, filename)
    new_device_id = db.new_device_id()
    device_info.extend([location, new_device_id, get_serial(port), port])
    db.add_to_database(device_info)
    current_app.logger.info(
        "[to_database] Device added: {}".format(device_info))


def check_if_out(location, port):
    """
    Checks to see if the port is registered for a device in the database.
    :param port: USB port
    :return: True or None
    """
    device_id = db.get_device_id_from_port(location, port)
    if device_id is None:
        current_app.logger.debug(
            "[check_if_out] Port {} is not registered to a device.".
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
    :param user_info: First Name, Last Name, SlackID, location
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
    device_name = db.get_device_name(device_id, location, port)
    if device_name is None:
        current_app.logger.debug(
            "[get_device_name] Unable to get device name from port - trying ID."
        )
        device_name = db.get_device_name_from_id(location, device_id)
    return device_name
