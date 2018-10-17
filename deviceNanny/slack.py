#
# Slack Messages
# Hudl
#
# Created by Ethan Seyl 2016
#

import logging
from slacker import Slacker

from flask import current_app


class NannySlacker:
    def __init__(self):
        self.channel = current_app.config['SLACK_CHANNEL']
        self.team_channel = current_app.config['SLACK_TEAM_CHANNEL']
        self.slack = Slacker(current_app.config['SLACK_API_KEY'])

    def help_message(self, device_name):
        """
        Sends a message to the device checkout slack channel that a device was taken
        without being checked out.
        :param device_name: Name of device taken
        """
        text = "`{}` was taken without being checked out! Please remember to enter your name or ID " \
               "after taking a device.".format(device_name)
        self.slack.chat.post_message(
            self.channel,
            attachments=[{
                "pretext": "Missing Device",
                "fallback": "Message from DeviceNanny",
                "text": text
            }])
        logging.debug("[help_message] Help message sent.")

    def user_reminder(self, slack_id, time_difference, device_name):
        """
        Sends a checkout expired reminder.
        :param slack_id: ID of user who checked out device
        :param time_difference: Time since device was checked out
        :param device_name: Name of expired device
        """
        text = "It's been *{}* since you checked out `{}`. Please renew your checkout online or return it " \
               "to the device lab.".format(time_difference, device_name)
        try:
            self.slack.chat.post_message(
                slack_id,
                attachments=[{
                    "pretext": "Checkout Reminder",
                    "fallback": "Message from DeviceNanny",
                    "text": text
                }])
            logging.debug("[user_reminder] Reminder sent.")
        except Exception as e:
            logging.warning("[user_reminder] Incorrect Slack ID. {}".format(e))

    def check_out_notice(self, user_info, device):
        """
        Sends a slack message confirming a device was checked out.
        :param user_info: First Name, Last Name, SlackID, location of user who checked out device
        :param device: Device taken
        """
        try:
            self.slack.chat.post_message(
                user_info['SlackID'],
                "You checked out `{}`. Checkout will expire after 3 days. Remember to plug the "
                "device back in when you return it to the lab. You can renew your checkout from "
                "the DeviceNanny web page.".format(device),
                as_user=False,
                username="DeviceNanny")
            self.slack.chat.post_message(
                self.channel,
                "*{} {}* just checked out `{}`".format(
                    user_info['first_name'], user_info['last_name'], device),
                as_user=False,
                username="DeviceNanny")
            logging.debug("[check_out_notice] Checkout message sent.")
        except Exception as e:
            current_app.logger.debug("[check_out_notice] Check out notice NOT sent. {}".format(e))

    def check_in_notice(self, user_info, device):
        """
        Sends a slack message confirming a device was checked in.
        :param user_info: First Name, Last Name, SlackID, location of user who checked in device
        :param device: Device returned
        """
        try:
            if user_info["first_name"] != "Missing":
                logging.debug("[check_in_notice] SlackID from user_info: {}".format(
                    user_info['SlackID']))
                self.slack.chat.post_message(
                    user_info['SlackID'],
                    "You checked in `{}`. Thanks!".format(device),
                    as_user=False,
                    username="DeviceNanny")
                self.slack.chat.post_message(
                    self.channel,
                    "*{} {}* just checked in `{}`".format(
                        user_info['first_name'],
                        user_info['last_name'], device),
                    as_user=False,
                    username="DeviceNanny")
                logging.debug(
                    "[check_in_notice] {} {} just checked in {}".format(
                        user_info['first_name'],
                        user_info['LastName'], device))
        except Exception as e:
            current_app.logger.debug("[check_in_notice] Check in message not sent. {}".format(e))

    def post_to_channel(self, device_id, time_difference, firstname, lastname):
        """
        Sends a slack message to the device checkout channel with an update for an expired checkout.
        :param device_id: Device ID of device taken
        :param time_difference: Time since device was checked out
        :param firstname: First name of user with expired checkout
        :param lastname: Last name of user with expired checkout
        """
        self.slack.chat.post_message(
            self.channel,
            '`{}` was checked out *{}* ago by *{} {}*'.format(
                device_id, time_difference, firstname, lastname),
            as_user=False,
            username="DeviceNanny")
        logging.debug("[post_to_channel] Posted to channel.")

    def nanny_check_in(self, device_name):
        """
        Sends slack message to the device checkout channel. Sent when the Nanny discovers a
        connected device that wasn't checked in.
        :param device_name: Name of device checked in
        """
        self.slack.chat.post_message(
            self.channel,
            "`{}` was checked in by the Nanny.".format(device_name),
            as_user=False,
            username="DeviceNanny")
        logging.debug("[nanny_check_in] Nanny check-in message sent.")

    def missing_device_message(self, device_name, time_difference):
        """
        Send a message to the location channel about a device that's been missing from the lab
        for more than the set checkout time.
        :param device_name:
        :param time_difference:
        :return:
        """
        self.slack.chat.post_message(
            self.team_channel,
            "`{}` has been missing from the device lab for `{}`. If you have it, please return the device to the lab "
            "and check it out under your name.".format(device_name, time_difference),
            as_user=False,
            username="DeviceNanny")
        logging.info(
            "[missing_device_message] Slack reminder sent to team channel for {}".
            format(device_name))
