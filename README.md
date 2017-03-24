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

6. Install MySQL server:
    - `sudo apt-get install mysql-server -y`
    - Create password for root user when prompted

7. Install PyMySQL:
    - `sudo pip3 install PyMySQL`

8. Install Apache2:
    - `sudo apt-get install apache2 php5 libapache2-mod-php5 -y`

9. Install PHPMyAdmin:
    - `sudo apt-get install phpmyadmin -y`
    - Select Apache2 as the server to use
    - Select Yes to configure database to PHPMyAdmin
    - Enter the root password entered for MySQL
    - Enter a password for PHPMyAdmin

10. Edit Apache to include PHPMyAdmin:
    - `sudo nano /etc/apache2/apache2.conf`
    - At the bottom of the file, add `Include /etc/phpmyadmin/apache.conf` then save and exit
    - Restart apache2 `sudo /etc/init.d/apache2 restart`
    
11. Test PHPMyAdmin:
    - Go to http://localhost/phpmyadmin
    - You should reach the login page where you can login as root
   

**Create Database and Web User**

1. Log in to http://localhost/phpmyadmin

2. Create a new database called `DeviceNanny`

3. Create a new user for web front end with read only privileges
    - Go to the Privileges tab
    - Click Add User
    - Create a new user with at least `Select` and `Update` privileges under Data

**Download and Configure DeviceNanny**

1. Clone the repo to your home directory (/home/pi/)
    - Go to the home directory: `cd`
    - Clone the repo: `git clone https://github.com/hudl/DeviceNanny`

2. Install requirements:
    - `sudo pip3 install -r ~/DeviceNanny/requirements.txt`

2. Copy file config/DeviceNanny.ini.template:
    - Paste and rename without .template extension
    - Add your database password
    - Add your Slack api key
    - Add your Slack device room ID
    
3. Copy file web/secretInfo.php.template:
    - Paste and rename without .template extension
    - Add the username and password for the web user
    
4. Import tables into database:
    - Login to `http://localhost/phpmyadmin`
    - Click into the DeviceNanny database
    - Go to the Import tab and choose to import `DeviceNannyDB.sql` in the `/resources` directory

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
    
**Enable Front-End**

1. Apache2 changes:
    - Open file `sudo nano /etc/apache2/sites-available/000-default.conf`
    - Change DocumentRoot to `/YOUR/PATH/TO/DeviceNanny/web/pages`
    - On the line under DocumentRoot add `DirectoryIndex devicenanny.php`
    - Save and exit
    - Open file `sudo nano /etc/apache2/apache2.conf`
    - Scroll down to the `<Directory>` section and add this below the last `</Directory>`
MAKE SURE TO CHANGE THE PATH
```
<Directory /PATH/TO/YOUR/DeviceNanny/web/pages/>
    Options FollowSymLinks
    AllowOverride None
    Require all granted
</Directory>
```

2. Restart apache2 `sudo systemctl apache2 restart`


**Add Users**

1. Login at http://localhost/phpmyadmin

2. Manually input users to the Users table
    
    

**Reboot and Configuration is COMPLETE**
