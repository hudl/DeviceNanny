#!/bin/bash
#
# Script triggered by UDEV
# Hudl
#
# Created by Ethan Seyl 2016
#
export DISPLAY=:0.0; export XAUTHORITY='/var/run/lightdm/root/:0'; sudo /home/pi/DeviceNanny/usb_checkout.py
