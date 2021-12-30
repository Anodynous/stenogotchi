# Stenogotchi
![stenogotchi_1](https://user-images.githubusercontent.com/17461433/107876588-8e52aa80-6ecf-11eb-81ba-14731c885ff1.jpeg)

Aim of the project is to deliver a cheap and portable device for running [Plover](https://www.openstenoproject.org/ "Plover: Open Steno Project") where local installation on the host is impossible or simply not preferred. A stand-alone link enabling stenography using any input device supported by Plover on any device accepting bluetooth keyboards. 

Likely use-cases include: 
- Mobile devices
- Corporate and public computers restricting software installations 
- Hassle-free switching between devices without the need to install and configure Plover
- On-the-go stenographic recording

Stenogotchi is built on top of [Pwnagotchi](https://github.com/evilsocket/pwnagotchi), but instead of hungering for WPA handshakes it feeds on your steno chords. It emulates a BT HID device for connecting to a host and output can be toggled between STENO and QWERTY mode on the fly. The friendly UI optimized for low-power eINK displays is also accessible as a web UI version, making both the eINK display and buttonSHIM modules optional. If the RPI0w always will be powered over microUSB a separate battery pack is not needed. The suggested UPS-Lite 1000 mAH battery provides 3+ hours of runtime and supports pass-through charging. 

## Hardware
| Module                                                                                                                                                                    | Status       |
|:--------------------------------------------------------------------------------------------------------------------------------------------------------------------------|:-------------|
| [Raspberry Pi Zero W](https://www.raspberrypi.org/products/raspberry-pi-zero-w/) or [Raspberry Pi Zero 2 W](https://www.raspberrypi.com/products/raspberry-pi-zero-2-w/)  | Required     |
| MicroSD card (min 4 GiB)                                                                                                                                                  | Required     |
| [Waveshare 2.13 v.2](https://www.waveshare.com/wiki/2.13inch_e-Paper_HAT)                                                                                                 | Recommended  |
| [ButtonSHIM](https://shop.pimoroni.com/products/button-shim)                                                                                                              | Recommended  |
| [UPS-Lite v1.2](https://hackaday.io/project/173847-ups-lite)                                                                                                              | Recommended  |
| [DS3231 RTC Module](https://www.pishop.us/product/ds3231-real-time-clock-module-for-raspberry-pi/)                                                                        | Optional     |

See the [build notes](BUILDNOTES.md) for guidance on fitting the parts together.
## Installation
All commands should be executed as root. The installation process can be completed headless.

1. Flash and configure DietPi image, see https://dietpi.com/docs/install/
    * For headless installation, set AUTO_SETUP_NET_WIFI_ENABLED=1 in dietpi.txt and enter wifi credentials in dietpi-wifi.txt before first boot.
    * When prompted allow dietpi to update, change passwords and disable serial console. Under dietpi-config > advanced options enable:
        * Bluetooth
        * SPI state (needed by eINK screen)
        * I2C state (needed by Buttonshim module and for UPS-Lite power readings)
    * Using command 'dietpi-autostart' enable automatic login of user 'root' to local terminal (option #7)

2. Install dependencies

       apt-get install git xorg xserver-xorg-video-fbdev python3-pip python3-rpi.gpio python3-gi libtiff5 libopenjp2-7 bluez screen rfkill -y
       pip3 install file_read_backwards flask flask-wtf flask-cors evdev python-xlib pillow spidev jsonpickle dbus-python toml

3. Download and install Plover (v4.0.0.dev10)

       wget https://github.com/openstenoproject/plover/releases/download/v4.0.0.dev10/plover-4.0.0.dev10-py3-none-any.whl
       pip3 install plover-4.0.0.dev10-py3-none-any.whl

   * If you'd rather try the [continuous build of Plover](https://github.com/openstenoproject/plover/releases/tag/continuous) for the latest improvements, you will need to install both build-essential and python3-dev through apt-get first. Switch back to dev10 if you experience issues.
4. Clone the Stenogotchi repository and install the plover plugin "stenogotchi_link"

       git clone https://github.com/Anodynous/stenogotchi.git
       pip3 install ./stenogotchi/plover_plugin/

5. Configure Plover. Setup will ultimately depend on your own preferences and keyboard, but below is what I use. Make sure to include at least 'auto_start = True' and the '[Plugins]' section in your own config.

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

6. Run installation script to finalize setup of Stenogotchi. Optional boot time improvements offered by script described in "Significantly reduce boot time" section below.
       
       chmod +x ./stenogotchi/initial_setup.sh
       ./stenogotchi/initial_setup.sh

7. Configure Stenogotchi settings after reboot completes

       nano /etc/stenogotchi/config.toml
        
       #----------modify the config as you see fit----------#
       main.plugins.buttonshim.enabled = true
       main.plugins.upslite.enabled = true
       main.plugins.evdevkb.enabled = true
       main.plugins.plover_link.bt_autoconnect_mac = '00:DE:AD:BE:EF:00,11:DE:AD:BE:EF:11'
       #----------

## Updating
       cd ~/stenogotchi
       git pull
       pip3 install ./stenogotchi/plover_plugin/

## Configuration / Troubleshooting
* Configuration files are placed in /etc/stenogotchi/. Create a separate file named config.toml containing overrides to the defaults. Don't edit default.toml directly as it will be overwritten on Stenogotchi version updates.
* The logfile is created in /var/log, which dietpi by default mounts to RAM to preserve the SD card lifespan. To make the file persistent across reboots it needs to be written to the disk. To aid with troubleshooting, either set the location to another existing folder using 'main.log.path' in config.toml or change the global dietpi setting using dietpi-software > Log System.
* If your target device expects a different input language or keyboard layout than US qwerty, use setxkbmap to align it. This should be added to the beginning of your .xinitrc file to run automatically at startup. For German language and dvorak layout for example the below would be used.

      setxkbmap -layout de -variant dvorak

### Bluetooth connections
* Define your bluetooth devices in main.plugins.plover_link.bt_autoconnect_mac to auto-connect on boot. Multiple comma-separated devices in order of priority can be given. If no connection attempts are successful at boot, the device will fall back to listening for incoming connection and pairing attempts.
* Only one active connection at a time is supported. To switch remote devices, disable bluetooth on the remote device and wait around 10 seconds before initiating a new connection. The Stenogotchi will attempt to reconnect to the lost device for a few seconds before falling back to listening for new incoming connections.
* Issues with pairing or connecting after changes in bluetooth configurations can normally be fixed through unpairing and re-pairing. On the Stenogotchi side this is best handled through bluetoothctl using the below process. Re-initiate pairing process from remote device after the pairing information has been cleared on both host and client side.
    
        bluetoothctl
        [bluetooth]# paired-devices
        Device 00:DE:AD:BE:EF:00 Anodynous' Ipad
        [bluetooth]# remove 00:DE:AD:BE:EF:00
        [bluetooth]# exit

### Significantly reduce boot time
* Set ARM initial turbo to the max (60s) under dietpi-config > performance options to reduce boot time. You can also play around with overclocking, throttling and cpu governor to find a suitable balance between performance and power draw.     
* Disable dietpi and apt update check at boot:
          
       nano /boot/dietpi.txt

       #----------	
       CONFIG_CHECK_DIETPI_UPDATES=0
       CONFIG_CHECK_APT_UPDATES=0
          
* Disable waiting for network and time sync at boot. Doing this you should be aware that the RPI0w does not have a hardware clock. It will lose track of real world time as soon it is powered off, making log timestamps or any time based action you may set up unreliable. None of this is important for the core functionality of the Stenogotchi and disabling time-sync at boot can shave up to a minute off the boot process. By adding a cheap I2C hardware clock you can completely remove the need for network sync. Many modules are small enough to fit in the empty space of the UPS-Lite or under the eINK screen. See the [build notes](BUILDNOTES.md) for more directions.
                        
       nano /boot/dietpi.txt
          
       #----------
       CONFIG_BOOT_WAIT_FOR_NETWORK=0
       CONFIG_NTP_MODE=0 

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
- [x] Improved web UI, including buttonSHIM functionality
- [ ] Plover chords for triggering Stenogotchi actions
- [ ] Dictionary additions using eINK screen
- [ ] Document configuration options and buttonSHIM functionality
- [ ] Clean up and optimize code, fix bugs and add test suite
- [ ] Expand Stenogotchi statuses, reactions and mood indicators
- [ ] On-the-fly updating and reloading of Plover dictionaries
- [ ] Simple AI for shaping personality of the Stenogotchi
- [ ] Proper usage and configuration documentation
- [ ] Support for other eINK display modules

## Pictures
![stenogotchi_3](https://user-images.githubusercontent.com/17461433/107877063-cb6c6c00-6ed2-11eb-9f92-9059acd9f66d.jpeg)
![stenogotchi_4](https://user-images.githubusercontent.com/17461433/107876793-e3db8700-6ed0-11eb-83bb-648b08d1a315.jpeg)
![stenogotchi_5](https://user-images.githubusercontent.com/17461433/107876790-e0480000-6ed0-11eb-820d-65188cd0a031.jpeg)

## License
Released under the GPL3 license.
