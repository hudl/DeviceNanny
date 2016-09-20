#!/usr/bin/env python3
#
# RFID Checkout
# Hudl
#
# Created by Ethan Seyl 2016
#

from db_actions import MyDB
import logging.config
import logging
import slack
import time


def rfid_scan(rfid_input):
    device_id = db.get_device_id_from_rfid(rfid_input)
    if device_id is False:
        print("Device not in system")
        logging.info("Device not in system")
        return False
    else:
        return device_id


def get_name():
    waiting_for_input = True
    while waiting_for_input:
        user_input = input(
            "Enter your first and last name OR your user ID number: ")
        try:
            int(user_input)
            waiting_for_input = False
            continue
        except ValueError:
            logging.debug("Not an integer")
        try:
            if all(x.isalpha() or x.isspace() for x in user_input):
                user_input = user_input.split(' ')
                if len(user_input) == 2:
                    waiting_for_input = False
                else:
                    print("Invalid entry...check spaces")
            else:
                print("Invalid entry")
        except ValueError:
            logging.debug("Not a valid name")
    user_info = db.user_info(user_input)
    if (user_info is None) or (user_info.get('FirstName') == '-'):
        print("Not a valid ID or Name")
        logging.debug("Not a valid ID or Name")
        return False
    return user_info


def check_if_out(device_id):
    is_out = db.checked_out_by(device_id)
    print(is_out)
    if is_out == 0:
        return False
    return True


def current_time():
    return int(time.time())


def check_in(user_info, device_id):
    db.rfid_check_in(device_id)

def check_out(user_info, device_id):
    db.check_out(user_info.get("UserID"), device_id)


def create_space():
    number = 5
    while number > 0:
        print("")
        number -= 1


def main():
    logging.info("Started")
    global db
    while True:
        rfid_input = input("Scan a device...")
        db = MyDB()
        device_id = rfid_scan(rfid_input)
        if device_id is False:
            continue
        else:
            print("Valid Device")
        device_name = db.get_device_name_from_id(device_id)
        user_info = get_name()
        while user_info is False:
            user_info = get_name()
        print("Valid ID")
        if check_if_out(device_id):
            check_in(user_info, device_id)
            slack.check_in_notice(user_info, device_name)
            print("{} checked in by {} {}.".format(device_name, user_info.get(
                'FirstName'), user_info.get('LastName')))
            create_space()
        else:
            check_out(user_info, device_id)
            slack.check_out_notice(user_info, device_name)
            print("{} checked out by {} {}.".format(device_name, user_info.get(
                'FirstName'), user_info.get('LastName')))
            create_space()


if __name__ == '__main__':
    logging.config.fileConfig("config/rfid_logging.conf")
    main()
