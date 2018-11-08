DeviceNanny is a device lab checkout system. It was designed with one goal in mind: be as reliable as possible. In fact, it's so reliable that you can't not use it. Devices are connected to the system via USB, and USB actions trigger the check-in, checkout, or device addition processes. Say hello to a fully charged device lab with an accurate inventory of available devices.

Features:
- Super simple checkout and check-in process triggered by USB connections/disconnections
- Every device is fully charged and ready
- Renew your expired checkouts through your browser
- Slackbot notifications when you check out/in a device
- Slackbot reminders to check in a device
- Monitor available devices, reliably, through your browser
- Channel alerts when a device is taken without being checked out
- Monitor device checkout activity in a Slack channel
- Easily add devices to the database by plugging them in
- RFID for devices not plugged in via USB
- Smart script to fix situations where devices could be taken/returned without being checked in/out


Hardware Requirements:
- Raspberry Pi (version 3 recommended)
- Raspberry Pi power supply
- Cool Raspberry Pi case
- USB hubs for power and data (must be able to power all connected devices)
- USB cords for all devices
- RFID reader (optional for devices that won't connect via USB)
- RFID tags (optional for devices that won't connect via USB)

Required packages if not using Debian Jessie:
- lightdm as default display manager
- zenity


**Configuring the Raspberry Pi from First Install**

1. Download and install the latest image of Raspbian Jessie from https://www.raspberrypi.org/downloads/raspbian/

2. Update settings in Raspberry Pi Configuration:
    - Open Raspberry Pi Configuration in the Menu or `sudo raspi-config`
    - Expand Filesystem
    - Disable Underscan if necessary
    - Set Localization options **(especially timezone)**
    - Reboot
    
3. Download and install system updates:
    - `sudo apt-get update && sudo apt-get upgrade -y`
    - `sudo reboot`
    
4. Disable screen from sleeping:
    - `sudo nano /etc/lightdm/lightdm.conf`
    - Change `#xserver-command=X` under the `[SeatDefaults]` header to this `xserver-command=X -s 0 -dpms` (make sure you uncomment the line)

5. **ESPECIALLY IMPORTANT** Disable auto-mounting USB devices:
    - `sudo nano ~/.config/pcmanfm/LXDE-pi/pcmanfm.conf`
    - Under `[volume]` change all options to `0`

    [volume]
    mount_on_startup=0
    mount_removable=0
    autorun=0
    
    - Reboot `sudo reboot`

NOTE: You might need to disable ModemManager as well, if you're using a different Linux distro.

**Download and Configure DeviceNanny**
1. Install necessary dependencies.
    - `sudo pip3 install virtualenv`
    - `sudo apt-get install nginx`
    
2. Clone the repo to your home directory (/home/pi/)
    - Go to the home directory: `cd`
    - Clone the repo: `git clone https://github.com/hudl/DeviceNanny`

3. Create virtualenv and install requirements.
    - `cd DeviceNanny && virtualenv venv`
    - `source venv/bin/activate`
    - `sudo pip install -r ~/DeviceNanny/requirements.txt`
    
4. Create .env file for secret tokens.
    - `nano deviceNanny/.env`
        ```bash
        SECRET_KEY=<some_secret_key>
        SLACK_API_KEY=<slack_api_key>
        ```
5. Create db and necessary tables
    - `export FLASK_APP=deviceNanny && export FLASK_ENV=production && flask init-db`
    
6. Create a systemd service unit file. By creating a systemd unit file it will allow the init system to automatically start Gunicorn and serve the Device Nanny application whenever the server boots.
   - `sudo nano /etc/systemd/system/devicenanny.service`
   ```bash
    [Unit]
    Description=Gunicorn instance to serve DeviceNanny
    After=network.target

    [Service]
    User=<user> # Update to your user
    Group=www-data
    WorkingDirectory=/<location to DeviceNanny> # Location to root directory of Device Nanny download
    Environment="PATH=/<location to DeviceNanny>/venv/bin"
    ExecStart=/<location to DeviceNanny>/venv/bin/gunicorn --workers 1 --bind unix:devicenanny.sock -m 007 "deviceNanny:create_app()"
    
    [Install]
    WantedBy=multi-user.target
   ```
   - Test systemd service file by starting and checking the status.
   
        `sudo systemctl start devicenanny && sudo systemctl status devicenanny`

7. Create a new server block configuration file in Nginx's site-available directory.
    - `sudo nano /etc/nginx/sites-available/devicenanny`
    ```bash
    server {
    listen 80;
    server_name devicenanny;

    location / {
        include proxy_params;
        proxy_pass http://unix:/<location to DeviceNanny>/devicenanny.sock;
       }
    }
    ```
    - Enable by symlinking to the site-enabled directory.
    
        `sudo ln -s /etc/nginx/sites-available/devicenanny /etc/nginx/sites-enabled`
    - Rename the default ngnix conf.
    
        `sudo mv /etc/nginx/sites-available/default /etc/nginx/sites-available/default.txt`
    - Restart the Nginx process.
     
        `sudo systemctl restart nginx`
    - If you encounter any errors, look under these logs.
    
        ```bash
        sudo less /var/log/nginx/error.log: checks the Nginx error logs.
        sudo less /var/log/nginx/access.log: checks the Nginx access logs.
        sudo journalctl -u nginx: checks the Nginx process logs.
        sudo journalctl -u devicenanny: checks your DeviceNannny Gunicorn logs
        ```
8. Open browser and naviate to http://yourpihostnamehere/
9. Go to settings page and update all fields with appropriate values.
10. Enjoy the greatest hardware managagment system in the world .

 
**Add UDEV Rule and Cron Job**

1. Copy file /resources/device_nanny.rules.template
    - Paste file without .template extension
    - Change the RUN= path to your DeviceNanny/start_checkout.sh location
    - Copy /resources/device_nanny.rules to /etc/udev/rules.d/
    - `sudo cp ~/DeviceNanny/resources/device_nanny.rules /etc/udev/rules.d/`

2. Add Cron job (needs sudo):
    - `sudo crontab -e`
    - If promted, choose your favorite text editor
    - Add `*/1 * * * * cd /YOUR/PATH/TO/DeviceNanny/ && ./nanny.py` to the end of the file
    - Save and exit

