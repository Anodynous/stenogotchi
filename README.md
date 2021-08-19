# Stenogotchi
![stenogotchi_1](https://user-images.githubusercontent.com/17461433/107876588-8e52aa80-6ecf-11eb-81ba-14731c885ff1.jpeg)

Aim of the project is to deliver a cheap and portable device for running [Plover](https://www.openstenoproject.org/ "Plover: Open Steno Project") where local installation on the host is impossible or simply not preferred. A stand-alone link enabling stenography using any input device supported by Plover on any device accepting bluetooth keyboards. 

Likely use-cases include: 
- Mobile devices
- Corporate and public computers restricting software installations 
- Hassle-free switching between devices without the need to install and configure Plover
- On-the-go stenographic recording

Stenogotchi is built on top of [Pwnagotchi](https://github.com/evilsocket/pwnagotchi), but instead of hungering for WPA handshakes it feeds on your steno chords. It emulates a BT HID device for connecting to a host and output can be toggled between STENO and QWERTY mode on the fly. The friendly UI optimized for low-power eINK displays is also accessible as a web-ui version, making both the eINK display and buttonSHIM modules optional. If the RPI0w always will be powered over microUSB a separate battery pack is not needed. The suggested UPS-Lite 1000 mAH battery provides 3+ hours of runtime and can be connected/disconnected to an external power source without interrupting operations. 

## Hardware
| Module                                                                           | Status       |
|:---------------------------------------------------------------------------------|:-------------|
| [Raspberry Pi Zero W](https://www.raspberrypi.org/products/raspberry-pi-zero-w/) | Required     |
| MicroSD card                                                                     | Required     |
| [Waveshare 2.13 v.2](https://www.waveshare.com/wiki/2.13inch_e-Paper_HAT)        | Recommended  |
| [ButtonSHIM](https://shop.pimoroni.com/products/button-shim)                     | Recommended  |
| [UPS-Lite v1.2](https://hackaday.io/project/173847-ups-lite)                     | Recommended  |

## Installation
All commands should be executed as root. The installation process can be completed headless.

1. [35min] Flash DietPi image, see https://dietpi.com/docs/install/
    * Enable and connect onboard wifi and let dietpi update
        * Can be done under dietpi-config > network options: adapters or using /boot/dietpi.txt and /boot/dietpi-wifi.txt. 
    * Under dietpi-config > advanced options enable:
        * Bluetooth
        * SPI state (needed by eINK screen)
        * I2C state (needed by Buttonshim and UPS-Lite power readings)

2. [15min] Install the following through dietpi-software > software additional
    * X Org X Server
    * Python 3 pip
    * Git Client

3. [5min] Install additional dependencies

       apt-get install xserver-xorg-video-fbdev libtiff5 libopenjp2-7 bluez python3-rpi.gpio python3-gi screen rfkill -y
       pip3 install file_read_backwards flask flask-wtf flask-cors evdev python-xlib pillow spidev jsonpickle pydbus dbus-python

4. Download and install Plover (v4.0.0.dev10)

       wget https://github.com/openstenoproject/plover/releases/download/v4.0.0.dev10/plover-4.0.0.dev10-py3-none-any.whl
       pip3 install plover-4.0.0.dev10-py3-none-any.whl

5. Clone the Stenogotchi repository and install the plover plugin "stenogotchi_link"

       git clone https://github.com/Anodynous/stenogotchi.git
       pip3 install ./stenogotchi/plover_plugin/

6. Add configuration file for D-Bus service used to communicate between Stenogotchi and plover plugin
        
       cp ./stenogotchi/plover_plugin/stenogotchi_link/com.github.stenogotchi.conf /etc/dbus-1/system.d/

7. Remove the input bluetooth plugin so that it does not grab the sockets we require access to. We make this the default behaviour by appending '-P input' to the pre-existing line in below service file.
	
       nano /lib/systemd/system/bluetooth.service
        
       #----------
       ExecStart=/usr/lib/bluetooth/bluetoothd -P input
        

8. Configure Plover and Stenogotchi to start at boot
    * Using dietpi-autostart enable automatic login of root to the local terminal
    * Automatically start Stenogotchi and X server at local terminal login

          nano ~/.bash_profile
    
          #----------
          if [[ -z $DISPLAY ]] && [[ $(tty) = /dev/tty1 ]]; then
            screen -S stenogotchi -dm python3 /root/stenogotchi/stenogotchi.py --debug
            xinit
          fi

    * Start Plover automatically at launch of X server

          nano ~/.xinitrc
          
          #----------
          screen -S plover plover -g none -l debug

9. Configure Plover. Setup will ultimately depend on your own preferences and keyboard, but below is what I use. Make sure to include at least 'auto_start = True' and the '[Plugins]' section in your own config.

        mkdir -p /root/.config/plover/
        nano /root/.config/plover/plover.cfg
        
        #----------
        [Output Configuration]
        space_placement = After Output
        start_attached = True
        start_capitalize = False
        undo_levels = 30

        [Logging Configuration]
        enable_stroke_logging = False
        enable_translation_logging = False

        [Machine Configuration]
        auto_start = True
        machine_type = Gemini PR

        [Gemini PR]
        baudrate = 9600
        bytesize = 8
        parity = N
        port = /dev/ttyACM0
        stopbits = 1
        timeout = 2.0

        [Plugins]
        enabled_extensions = ["stenogotchi_link"]

10. Launch Stenogotchi manually for initial setup. Configure settings after reboot completes.

        python3 ./stenogotchi/stenogotchi.py
        nano /etc/stenogotchi/config.toml
        
        #----------modify the config as you see fit----------#
        main.plugins.buttonshim.enabled = true
        main.plugins.upslite.enabled = true
        main.plugins.evdevkb.enabled = true
        main.plugins.plover_link.bt_autoconnect_mac = '00:DE:AD:BE:EF:00,11:DE:AD:BE:EF:11'
        #----------

11. Significantly reduce boot time
    * Set ARM initial turbo to the max (60s) under dietpi-config > performance options to reduce boot time. You can also play around with overclocking, throttling and cpu governor to find a suitable balance between performance and power draw.     
    * Disable dietpi and apt update check at boot:
          
          nano /boot/dietpi.txt

          #----------	
          CONFIG_CHECK_DIETPI_UPDATES=0
          CONFIG_CHECK_APT_UPDATES=0

    * Disable waiting for network and time sync at boot. Doing this you should be aware that the RPI0w does not have a hardware clock. It will lose track of real world time as soon it is powered off, making log timestamps or any time based action you may set up unreliable. None of this is important for the core functionality of the Stenogotchi and disabling time-sync at boot can shave up to a minute off the boot process. By adding a cheap I2C hardware clock you can completely remove the need for network sync. Many modules are small enough to fit in the empty space of the UPS-Lite or under the eINK screen [and are easy to wire](https://www.pishop.us/product/ds3231-real-time-clock-module-for-raspberry-pi/) and [set up](https://learn.adafruit.com/adding-a-real-time-clock-to-raspberry-pi/set-rtc-time). Just don't forget to isolate it with some tape. Here you can see [how to wire and fit the DS3231 module in the Stenogotchi](https://user-images.githubusercontent.com/17461433/111912767-cff8e700-8a73-11eb-9bd0-a406bd7241ef.jpg).
                        
          nano /boot/dietpi.txt
          
          #----------
          CONFIG_BOOT_WAIT_FOR_NETWORK=0
          CONFIG_NTP_MODE=0 

## Configuration
* Configuration files are placed in /etc/stenogotchi/. Create a separate file named config.toml containing overrides to the defaults. Don't edit default.toml directly as it will be overwritten on Stenogotchi version updates.

* Define your bluetooth devices in main.plugins.plover_link.bt_autoconnect_mac to auto-connect on boot. Multiple comma separated devices in order of priority can be given. If no connection attempts are successful, the device will fall back to listening for incoming connection attempts.
  * Issues with pairing or connecting after changes in bluetooth configurations can usually be fixed through unpairing and re-pairing. On the Stenogotchi side this is best handled through bluetoothctl.
    
        bluetoothctl
        [bluetooth]# paired-devices
        Device 00:DE:AD:BE:EF:00 Anodynous' Ipad
        [bluetooth]# remove 00:DE:AD:BE:EF:00
        [bluetooth]# exit

## Updating
       cd ~/stenogotchi
       git pull
       pip3 install ./stenogotchi/plover_plugin/

## Usage
![stenogotchi_2](https://user-images.githubusercontent.com/17461433/107883149-d5539680-6ef5-11eb-86fe-41f0b6293eed.jpg)

### Buttonshim
Below long-press (1s) actions are pre-defined. Short-press triggers user configurable terminal commands, e.g. rclone sync of Plover dictionaries with cloud storage.
 
* Button A - toggle QWERTY / STENO mode
* Button B - toggle wpm & strokes readings
* Button C - toggle dictionary lookup mode
* Button D - toggle wifi (reboot persistent)
* Button E - shutdown

## Project roadmap
- [x] Proof of concept. Headless RPI0W running Plover, emulating bluetooth HID device and seamlessly piping steno output over BT to host
- [x] Create proper plugin for integration with Plover
- [x] Integrate bluetooth HID server as Stenogotchi plugin
- [x] Support for eINK display and web UI
- [x] Support for buttons for built-in and user customizable actions
- [x] Support for external battery charge readings on UI
- [x] Create Stenogotchi plugin to capture QWERTY input while blocking Plover
- [x] ButtonSHIM toggle to enable/disable WIFI, persisting reboot
- [x] ButtonSHIM toggle between STENO and QWERTY output mode
- [x] WPM readings for STENO mode
- [x] Full installation guide for Plover and Stenogotchi using DietPi as base image
- [x] Dictionary lookup using eINK screen
- [x] Decrease steno latency
- [ ] Plover chords for triggering Stenogotchi actions
- [ ] Dictionary additions using eINK screen
- [ ] Document configuration options and buttonSHIM functionality
- [ ] Clean up and optimize code, fix bugs and add test suite
- [ ] Expand Stenogotchi statuses, reactions and mood indicators
- [ ] On-the-fly updating and reloading of Plover dictionaries
- [ ] Improved web-ui, including buttonSHIM functionality
- [ ] Simple AI for shaping personality of the Stenogotchi
- [ ] Proper usage and configuration documentation
- [ ] Support for other eINK display modules

## Pictures
![stenogotchi_3](https://user-images.githubusercontent.com/17461433/107877063-cb6c6c00-6ed2-11eb-9f92-9059acd9f66d.jpeg)
![stenogotchi_4](https://user-images.githubusercontent.com/17461433/107876793-e3db8700-6ed0-11eb-83bb-648b08d1a315.jpeg)
![stenogotchi_5](https://user-images.githubusercontent.com/17461433/107876790-e0480000-6ed0-11eb-820d-65188cd0a031.jpeg)

## License
Released under the GPL3 license.
