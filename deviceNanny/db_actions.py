from deviceNanny.db import get_db
from flask import current_app


def db_fetch(string):
    try:
        db = get_db()
        item = db.execute(string).fetchone()
        return item
    except Exception as e:
        current_app.logger.error("[db_fetch] Exception - {}".format(e))


def db_fetch_all(string):
    try:
        db = get_db()
        cur = db.execute(string)
        item = cur.fetchall()
        return item
    except Exception as e:
        current_app.logger.error(
            "[db_fetch_all] Exception - {}".format(e))


def db_commit(string):
    try:
        db = get_db()
        db.execute(string)
        db.commit()
    except Exception as e:
        current_app.logger.error("[db_commit] Exception - {}".format(e))
        print(e)


def new_device_id():
    """
    :return: Highest device_id in devices table + 1
    """
    try:
        last_id_num = db_fetch("SELECT device_id from devices where device_id=(SELECT max(device_id) FROM devices)")
        id_number = last_id_num['device_id'] + 1
    except Exception as e:
        id_number = '0'
        current_app.logger.debug("[new_device_id] {}".format(id_number))
        print(e)
    return id_number


def device_ids():
    """
    :return: All device_ids from devices table.
    """
    devices = db_fetch_all("SELECT device_id from devices")
    return devices


def checked_out_by(device_id):
    """
    :param device_id:
    :return: UserID
    """
    user_info = db_fetch("SELECT checked_out_by from devices WHERE device_id = {}".format(int(device_id)))
    current_app.logger.debug("[checked_out_by] device_id {} checked out by {}".format(
        device_id, user_info["checked_out_by"]))
    return user_info["checked_out_by"]


def get_device_name(location, port):
    """
    :param port: USB port
    :param location: location
    :return: device_name
    """
    try:
        device = db_fetch("SELECT device_name from devices WHERE port = '{}' AND location = '{}'".format(port, location))
        return device["device_name"]
    except Exception as e:
        current_app.logger.debug(
            "[get_device_name] Exception - {}".format(e))
        print(e)


def get_device_name_from_id(device_id):
    """
    :param device_id:
    :return: device_name
    """
    # logging.debug(
    #     "[get_device_name_from_id] Device ID = {}, location = {}".
    #     format(device_id, location))
    location = current_app.config['location']
    try:
        device = db_fetch("SELECT device_name from devices WHERE device_id = '{}' AND location = '{}'"
                          .format(device_id, location))
        current_app.logger.debug("[get_device_name_from_id] Device Name: {}".format(device["device_name"]))
        return device["device_name"]
    except Exception as e:
        current_app.logger.error("[get_device_name_from_id] Exception - {}".format(e))
        print(e)


def get_device_id_from_port(location, port):
    """
    :param port:
    :param location:
    :return: device_id
    """
    current_app.logger.debug("[get_device_id_from_port] Port: {} Location: {}".format(port, location))
    device = db_fetch("SELECT device_id from devices WHERE location = '{}' AND port = '{}'".format(location, port))
    try:
        return device["device_id"]
    except Exception as e:
        current_app.logger.debug("[get_device_id_from_port] No device ID for port {}. {}".format(port, e))
        pass


def get_port_from_device_id(device_id):
        """
        :param device_id:
        :return: port
        """
        port = db_fetch("SELECT port from devices WHERE device_id = '{}'".format(device_id))
        try:
            return port["port"]
        except Exception as e:
            current_app.logger.debug("[get_port_from_device_id] No port registered for device {}".format(device_id))
            print(e)


def get_device_id_from_serial(serial):
    """
    :param serial:
    :return: device_id
    """
    device = db_fetch("SELECT device_id from devices WHERE serial_udid = '{}'".format(serial))
    try:
        return device["device_id"]
    except TypeError as e:
        current_app.logger.info("[get_device_id_from_serial] "
                                "No device ID for serial {}: {}".format(serial, e))


def user_info(user_input):
    """
    :param user_input: first_name last_name OR UserID
    :return: first_name, last_name, SlackID, location, UserID
    """
    # logging.debug([user_info] user_input = {}. device_type = {}".format(user_input, type(user_input)))
    try:
        int(user_input[0])
        user_info = db_fetch("SELECT * FROM users WHERE id = {}".format(user_input[0]))
        current_app.logger.info("[user_info] id input. Checked out by {}".format(user_info['first_name']))
        return False, user_info
    except Exception as e:
        try:
            user_info = db_fetch("SELECT * from users WHERE first_name = '{}' AND last_name = '{}'"
                                 .format(str(user_input[0]), str(user_input[1])))
            print("Your id is: {}".format(user_info["id"]))
            current_app.logger.info("[user_info] User name input. Checked out by {}".format(user_info['first_name']))
            return False, user_info
        except Exception as e:
            current_app.logger.info('[user_info] User not found. {}'.format(e))
            return True, {'first_name': str(user_input[0]), 'last_name': str(user_input[1]), 'id': None}


def update_time_reminded(device_name):
    """
    Updates database with the last time a reminder was sent.
    :param device_name:
    """
    db_commit("UPDATE devices set last_reminded = unix_timestamp() where device_name = '{}'".format(device_name))
    current_app.logger.info("[update_time_reminded] last_reminded has been reset to current time.")


def clear_port(device_id):
    """
    Sets the port for a device to NULL.
    :param device_id:
    """
    db_commit("UPDATE devices set port = NULL where device_id = {}".format(device_id))


def add_to_database(device_info):
    """
    Adds info for a new device to the database.
    :param device_info:
    """
    db_commit("INSERT INTO devices(device_name,manufacturer,model,device_type,os_version,location,device_id,serial_udid,port,"
              "checked_out_by,time_checked_out,last_reminded)"
              "VALUES('{}','{}','{}','{}','{}','{}','{}','{}','{}','0','0','40000')"
              .format(device_info[0], device_info[1], device_info[2], device_info[3], device_info[4].rstrip(),
                      device_info[5], device_info[6], device_info[7], device_info[8]))


def add_user_to_database(user_info):
    """
    Adds a new user into the users database.
    :param user_info: List with first_name, last_name, slack_id, and location
    """
    try:
        db_commit("INSERT INTO users(first_name,last_name,slack_id,location)VALUES('{}', '{}', '{}', '{}')".format(
            user_info['first_name'], user_info['last_name'], user_info['slack_id'], user_info['location']))
    except Exception as e:
        current_app.logger.debug('[add_user_to_database] Exception: {}'.format(e))


def get_user_id()


def check_in(device_id, port):
    """
    Updates database with check in info.
    :param device_id:
    :param port:
    """
    try:
        db_commit("UPDATE devices SET checked_out_by = '--', port = '{}' where device_id = {}".format(port, device_id))
    except Exception as e:
        current_app.logger.debug("[check_in] Exception - {}".format(e))
        print(e)


def check_out(first_name, last_name, device_id):
    """
    Updates database with check out info.
    :param user_id: User checking out device. Missing device ID is 2
    :param device_id: Device ID of device getting checked out
    """
    current_app.logger.debug('[check_out] user_id: {} device_id: {}'.format(user_id, device_id))
    try:
        db_commit("UPDATE devices SET checked_out_by = {} {}, port = NULL, time_checked_out = strftime('%s', 'now'),"
                  "last_reminded = strftime('%s', 'now') where device_id = {}".format(first_name, last_name, device_id))
    except Exception as e:
        current_app.logger.error("[check_out] FAILED TO CHECK OUT DEVICE - {}".format(e))


def get_device_status(device_id):
    """
    Returns all columns for a device.
    :param device_id:
    :return: device_name, checked_out_by, time_checked_out, last_reminded
    """
    device_status = db_fetch("SELECT device_name, checked_out_by, time_checked_out, last_reminded,"
                             "location FROM devices WHERE device_id = {}".format(device_id))
    current_app.logger.debug("[get_device_status] DEVICE STATUS: {}".format(device_status))
    return device_status


def get_slack_id(user_id):
    """
    :param user_id:
    :return: SlackID for user
    """
    slack_id = db_fetch("SELECT slack_id FROM users WHERE id = {}".format(user_id))
    return slack_id


def get_registered_ports(location):
    """
    :return: USB ports for each device in database
    """
    ports = db_fetch_all("SELECT port from devices where port is not Null AND location = '{}'".format(location))
    return ports


def get_serial_number_from_port(location, port):
    """
    :param port:
    :param location:
    :return: Serial number
    """
    try:
        serial = db_fetch("SELECT serial_udid FROM devices WHERE port = '{}' AND location = '{}'".format(port, location))
        return serial["serial_udid"]
    except Exception as e:
        current_app.logger.debug('[get_serial_number_from_port] No serial for port {} - {}'.format(port, e))
