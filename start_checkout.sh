#!/bin/bash
#
# Script triggered by UDEV
# Hudl
#
# Created by Ethan Seyl 2016
#
export DISPLAY=:0.0;
export XAUTHORITY='/var/run/lightdm/root/:0';
#sudo /YOUR/PATH/TO/DeviceNanny/usb_checkout.py

curl http://127.0.0.1:5000/api/devices/detected