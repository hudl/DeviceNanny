from deviceNanny.db import get_db


def db_fetch(string):
    try:
        db = get_db()
        cur = db.execute(string)
        item = cur.fetchone()
        return item
    except Exception as e:
        # logging.error("[db_actions][db_fetch] Exception - {}".format(e))
        print(e)


def db_fetch_all(string):
    try:
        db = get_db()
        cur = db.execute(string)
        item = cur.fetchall()
        return item
    except Exception as e:
        # logging.error(
        #     "[db_actions][db_fetch_all] Exception - {}".format(e))
        print(e)


def db_commit(string):
    try:
        db = get_db()
        db.execute(string)
        db.commit()
    except Exception as e:
        # logging.error("[db_actions][db_commit] Exception - {}".format(e))
        print(e)


def new_device_id():
    """
    :return: Highest DeviceID in Devices table + 1
    """
    try:
        last_id_num = db_fetch("SELECT DeviceID from Devices where DeviceID=(SELECT max(DeviceID) FROM Devices)")
        id_number = last_id_num.get('DeviceID') + 1
    except Exception as e:
        id_number = '0'
        # logging.debug("[db_actions][new_device_id] {}".format(id_number))
        print(e)
    return id_number


def device_ids():
    """
    :return: All DeviceIDs from Devices table.
    """
    devices = db_fetch_all("SELECT DeviceID from Devices")
    return devices


def checked_out_by(device_id):
    """
    :param device_id:
    :return: UserID
    """
    user_info = db_fetch("SELECT CheckedOutBy from Devices WHERE DeviceID = {}".format(int(device_id)))
    # logging.debug("[db_actions][checked_out_by] DeviceID {} checked out by {}"
    #               .format(device_id, user_info.get("CheckedOutBy")))
    return user_info.get("CheckedOutBy")


def get_device_name(location, port):
    """
    :param port: USB port
    :param location: Location
    :return: DeviceName
    """
    try:
        device = db_fetch("SELECT DeviceName from Devices WHERE Port = '{}' AND Location = '{}'".format(port, location))
        return device.get("DeviceName")
    except Exception as e:
        # logging.debug(
        #     "[db_actions][get_device_name] Exception - {}".format(e))
        print(e)


def get_device_name_from_id(location, device_id):
    """
    :param device_id:
    :return: DeviceName
    """
    # logging.debug(
    #     "[db_actions][get_device_name_from_id] Device ID = {}, Location = {}".
    #     format(device_id, location))
    try:
        device = db_fetch("SELECT DeviceName from Devices WHERE DeviceID = '{}' AND Location = '{}'".format(device_id, location))
        # logging.debug("[db_actions][get_device_name_from_id] Device Name: {}".format(device.get("DeviceName")))
        return device.get("DeviceName")
    except Exception as e:
        # logging.error("[db_actions][get_device_name_from_id] Exception - {}".format(e))
        print(e)


def get_device_id_from_port(location, port):
    """
    :param port:
    :param location:
    :return: DeviceID
    """
    device = db_fetch("SELECT DeviceID from Devices WHERE Location = '{}' AND Port = '{}'".format(location, port))
    try:
        return device.get("DeviceID")
    except AttributeError:
        pass


def get_port_from_device_id(device_id):
        """
        :param device_id:
        :return: Port
        """
        port = db_fetch("SELECT Port from Devices WHERE DeviceID = '{}'".format(device_id))
        try:
            return port.get("Port")
        except Exception as e:
            # logging.debug("[db_actions][get_port_from_device_id] No port registered for device {}".format(device_id))
            print(e)


def get_device_id_from_serial(serial):
    """
    :param serial:
    :return: DeviceID
    """
    device = db_fetch("SELECT DeviceID from Devices WHERE SerialUDID = '{}'".format(serial))
    try:
        return device.get("DeviceID")
    except AttributeError:
        pass


def user_info(user_input):
    """
    :param user_input: FirstName LastName OR UserID
    :return: FirstName, LastName, SlackID, Location, UserID
    """
    # logging.debug("[db_actions][user_info] user_input = {}. Type = {}".format(user_input, type(user_input)))
    try:
        int(user_input[0])
        user_info = db_fetch("SELECT * from Users WHERE UserID = {}".format(user_input[0]))
        # logging.info("[db_actions][user_info] UserID input. Checked out by {}".format(user_info))
        return user_info
    except Exception as e:
        try:
            user_info = db_fetch("SELECT * from Users WHERE FirstName = '{}' AND LastName = '{}'".format(str(user_input[0]), str(user_input[1])))
            print("Your UserID is: {}".format(user_info.get("UserID")))
            # logging.info("[db_actions][user_info] User name input. Checked out by {}".format(user_info))
            return user_info
        except Exception as e:
            print(e)


def update_time_reminded(device_name):
    """
    Updates database with the last time a reminder was sent.
    :param device_name:
    """
    db_commit("UPDATE Devices set LastReminded = unix_timestamp() where DeviceName = '{}'".format(device_name))
    # logging.info("[db_actions][update_time_reminded] LastReminded has been reset to current time.")


def clear_port(device_id):
    """
    Sets the port for a device to NULL.
    :param device_id:
    """
    db_commit("UPDATE Devices set Port = NULL where DeviceID = {}".format(device_id))


def add_to_database(device_info):
    """
    Adds info for a new device to the database.
    :param device_info:
    """
    db_commit("INSERT INTO Devices(DeviceName,Manufacturer,Model,Type,OS,Location,DeviceID,SerialUDID,Port,CheckedOutBy, TimeCheckedOut,LastReminded) VALUES('{}','{}','{}','{}','{}','{}','{}','{}','{}','0','0','40000')".format(device_info[0], device_info[1], device_info[2], device_info[3], device_info[4].rstrip(), device_info[5], device_info[6], device_info[7], device_info[8]))


def check_in(device_id, port):
    """
    Updates database with check in info.
    :param device_id:
    :param port:
    """
    try:
        db_commit("UPDATE Devices set CheckedOutBy = '0', Port = '{}' where DeviceID = {}".format(port, device_id))
    except Exception as e:
        # logging.debug("[db_actions][check_in] Exception - {}".format(e))
        print(e)


def check_out(user_id, device_id):
    """
    Updates database with check out info.
    :param user_id:
    :param device_id:
    """
    try:
        db_commit("UPDATE Devices set CheckedOutBy = {}, Port = NULL, TimeCheckedOut = unix_timestamp(), LastReminded = unix_timestamp() where DeviceID = {}".format(user_id, device_id))
    except Exception as e:
        # logging.debug("[db_actions][check_out] Exception in check_out - {}".format(e))
        print(e)


def get_device_status(device_id):
    """
    Returns all columns for a device.
    :param device_id:
    :return: DeviceName, CheckedOutBy, TimeCheckedOut, LastReminded
    """
    device_status = db_fetch("SELECT DeviceName, CheckedOutBy, TimeCheckedOut, LastReminded, Location from Devices where DeviceID = {}".format(device_id))
    return device_status


def get_slack_id(user_id):
    """
    :param user_id:
    :return: SlackID for user
    """
    slack_id = db_fetch("SELECT SlackID from Users where UserID = {}".format(user_id))
    return slack_id


def get_registered_ports(location):
    """
    :return: USB Ports for each device in database
    """
    ports = db_fetch_all("SELECT Port from Devices where Port is not Null AND Location = '{}'".format(location))
    return ports


def get_serial_number_from_port(location, port):
    """
    :param port:
    :param location:
    :return: Serial number
    """
    serial = db_fetch("SELECT SerialUDID from Devices where Port = '{}' AND Location = '{}'".format(port, location))
    return serial.get("SerialUDID")
