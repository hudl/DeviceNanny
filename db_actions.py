#
# Database Calls
# Hudl
#
# Created by Ethan Seyl 2016
#

import pymysql.cursors
import configparser
import logging
import os


class MyDB(object):
    _db = None
    _db_cur = None
    _config = None
    _working_dir = None

    def __init__(self):
        self._working_dir = os.path.dirname(__file__)
        self._config = configparser.ConfigParser()
        self._config.read(
            '{}/config/DeviceNanny.ini'.format(self._working_dir))
        self._db = pymysql.connect(
            host=self._config['DATABASE']['host'],
            user=self._config['DATABASE']['user'],
            password=self._config['DATABASE']['password'],
            db=self._config['DATABASE']['name'],
            charset='utf8mb4',
            cursorclass=pymysql.cursors.DictCursor)
        self._db_cur = self._db.cursor()
        logging.debug("[db_actions][init] Connected to database successfully")

    def db_fetch(self, string):
        try:
            cur = self._db.cursor()
            cur.execute(string)
            item = cur.fetchone()
            return item
        except Exception as e:
            logging.error("[db_actions][db_fetch] Exception - {}".format(e))
        finally:
            cur.close()

    def db_fetch_all(self, string):
        try:
            cur = self._db.cursor()
            cur.execute(string)
            item = cur.fetchall()
            return item
        except Exception as e:
            logging.error(
                "[db_actions][db_fetch_all] Exception - {}".format(e))
        finally:
            cur.close()

    def db_commit(self, string):
        try:
            cur = self._db.cursor()
            cur.execute(string)
            self._db.commit()
        except Exception as e:
            logging.error("[db_actions][db_commit] Exception - {}".format(e))
        finally:
            cur.close()

    def new_device_id(self):
        """
        :return: Highest DeviceID in Devices table + 1
        """
        try:
            last_id_num = self.db_fetch(
                "SELECT DeviceID from Devices where DeviceID=(SELECT max(DeviceID) FROM Devices)"
            )
            id_number = last_id_num.get('DeviceID') + 1
        except:
            id_number = '0'
        logging.debug("[db_actions][new_device_id] {}".format(id_number))
        return id_number

    def device_ids(self):
        """
        :return: All DeviceIDs from Devices table.
        """
        devices = self.db_fetch_all("SELECT DeviceID from Devices")
        return devices

    def checked_out_by(self, device_id):
        """
        :param device_id:
        :return: UserID
        """
        user_info = self.db_fetch(
            "SELECT CheckedOutBy from Devices WHERE DeviceID = {}".format(
                int(device_id)))
        logging.debug(
            "[db_actions][checked_out_by] DeviceID {} checked out by {}".
            format(device_id, user_info.get("CheckedOutBy")))
        return user_info.get("CheckedOutBy")

    def get_device_name(self, location, port):
        """
        :param port: USB port
        :param location: Location
        :return: DeviceName
        """
        try:
            device = self.db_fetch(
                "SELECT DeviceName from Devices WHERE Port = '{}' AND Location = '{}'".
                format(location, port))
            return device.get("DeviceName")
        except Exception as e:
            logging.debug(
                "[db_actions][get_device_name] Exception - {}".format(e))

    def get_device_name_from_id(self, location, device_id):
        """
        :param device_id:
        :return: DeviceName
        """
        logging.debug(
            "[db_actions][get_device_name_from_id] Device ID = {}, Location = {}".
            format(device_id, location))
        try:
            device = self.db_fetch(
                "SELECT DeviceName from Devices WHERE DeviceID = '{}' AND Location = '{}'".
                format(device_id, location))
            logging.debug(
                "[db_actions][get_device_name_from_id] Device Name: {}".format(
                    device.get("DeviceName")))
            return device.get("DeviceName")
        except Exception as e:
            logging.error(
                "[db_actions][get_device_name_from_id] Exception - {}".format(
                    e))

    def get_device_id_from_port(self, location, port):
        """
        :param port:
        :param location:
        :return: DeviceID
        """
        device = self.db_fetch(
            "SELECT DeviceID from Devices WHERE Location = '{}' AND Port = '{}'".
            format(location, port))
        try:
            return device.get("DeviceID")
        except AttributeError:
            return None

    def get_port_from_device_id(self, device_id):
        """
        :param device_id:
        :return: Port
        """
        port = self.db_fetch(
            "SELECT Port from Devices WHERE DeviceID = '{}'".format(device_id))
        try:
            return port.get("Port")
        except:
            logging.debug(
                "[db_actions][get_port_from_device_id] No port registered for device {}".
                format(device_id))

    def get_device_id_from_serial(self, serial):
        """
        :param serial:
        :return: DeviceID
        """
        device = self.db_fetch(
            "SELECT DeviceID from Devices WHERE SerialUDID = '{}'".format(
                serial))
        try:
            return device.get("DeviceID")
        except AttributeError:
            return None

    def user_info(self, user_input):
        """
        :param user_input: FirstName LastName OR UserID
        :return: FirstName, LastName, SlackID, Location, UserID
        """
        logging.debug("[db_actions][user_info] user_input = {}. Type = {}".
                      format(user_input, type(user_input)))
        try:
            int(user_input[0])
            user_info = self.db_fetch(
                "SELECT * from Users WHERE UserID = {}".format(user_input[0]))
            logging.info(
                "[db_actions][user_info] UserID input. Checked out by {}".
                format(user_info))
            return user_info
        except:
            try:
                user_info = self.db_fetch(
                    "SELECT * from Users WHERE FirstName = '{}' AND LastName = '{}'".
                    format(str(user_input[0]), str(user_input[1])))
                print("Your UserID is: {}".format(user_info.get("UserID")))
                logging.info(
                    "[db_actions][user_info] User name input. Checked out by {}".
                    format(user_info))
                return user_info
            except:
                return None

    def update_time_reminded(self, device_name):
        """
        Updates database with the last time a reminder was sent.
        :param device_name:
        """
        self.db_commit(
            "UPDATE Devices set LastReminded = unix_timestamp() where DeviceName = '{}'".
            format(device_name))
        logging.info(
            "[db_actions][update_time_reminded] LastReminded has been reset to current time."
        )

    def clear_port(self, device_id):
        """
        Sets the port for a device to NULL.
        :param device_id:
        """
        self.db_commit("UPDATE Devices set Port = NULL where DeviceID = {}".
                       format(device_id))

    def add_to_database(self, device_info):
        """
        Adds info for a new device to the database.
        :param device_info:
        """
        self.db_commit(
            "INSERT INTO Devices(DeviceName,Manufacturer,Model,Type,OS,Location,DeviceID,SerialUDID,Port,CheckedOutBy,"
            "TimeCheckedOut,LastReminded) VALUES('{}','{}','{}','{}','{}','{}','{}','{}','{}','0','0','40000')".
            format(device_info[0], device_info[1], device_info[2],
                   device_info[3], device_info[4].rstrip(), device_info[5],
                   device_info[6], device_info[7], device_info[8]))

    def check_in(self, device_id, port):
        """
        Updates database with check in info.
        :param device_id:
        :param port:
        """
        try:
            self.db_commit("UPDATE Devices set CheckedOutBy = '0',"
                           "Port = '{}' where DeviceID = {}".format(
                               port, device_id))
        except Exception as e:
            logging.debug("[db_actions][check_in] Exception - {}".format(e))

    def check_out(self, user_id, device_id):
        """
        Updates database with check out info.
        :param user_id:
        :param device_id:
        """
        try:
            self.db_commit(
                "UPDATE Devices set CheckedOutBy = {}, Port = NULL,"
                "TimeCheckedOut = unix_timestamp(), LastReminded = unix_timestamp() where DeviceID = {}".
                format(user_id, device_id))
        except Exception as e:
            logging.debug(
                "[db_actions][check_out] Exception in check_out - {}".format(
                    e))

    def get_device_status(self, device_id):
        """
        Returns all columns for a device.
        :param device_id:
        :return: DeviceName, CheckedOutBy, TimeCheckedOut, LastReminded
        """
        device_status = self.db_fetch(
            "SELECT DeviceName, CheckedOutBy, TimeCheckedOut, LastReminded,"
            "Location from Devices where DeviceID = {}".format(device_id))
        return device_status

    def get_slack_id(self, user_id):
        """
        :param user_id:
        :return: SlackID for user
        """
        slack_id = self.db_fetch(
            "SELECT SlackID from Users where UserID = {}".format(user_id))
        return slack_id

    def get_registered_ports(self, location):
        """
        :return: USB Ports for each device in database
        """
        ports = self.db_fetch_all(
            "SELECT Port from Devices where Port is not Null AND Location = '{}'".
            format(location))
        return ports

    def get_serial_number_from_port(self, location, port):
        """
        :param port:
        :param location:
        :return: Serial number
        """
        serial = self.db_fetch(
            "SELECT SerialUDID from Devices where Port = '{}' AND Location = '{}'".
            format(port, location))
        return serial.get("SerialUDID")
