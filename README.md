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
| [UPS-Lite v1.2](https://hackaday.io/project/173847-ups-lite)                     | Optional     |

## Installation

1. Flash and setup DietPi image, see https://dietpi.com/docs/install/
    * Enable wifi, bluetooth and optionally set the boot boost to the max (60s)
    * Reboot and let dietpi update

2. Install the following through DietPi-Software
    * LXDE (alternatively install and configure X.Org X Server as the window manager shouldn't be needed)
    * Python 3 pip
    * Build-Essentials
    * Git Client

3. Manually install some additional dependencies
    
        >apt install python3-setuptools python3-pyqt5 qt5-default pyqt5-dev pyqt5-dev-tools screen -y
        >pip3 install dbus-python python-xlib==0.29

4. Clone the Plover repository and comment out dbus-python and PyQt5 from requirements_distribution

        >cd ~ 
        >git clone https://github.com/openstenoproject/plover.git
        >cd plover
        >nano requirements_distribution.txt
            ...
            #dbus-python==1.2.4; "linux" in sys_platform
            #PyQt5-sip==4.19.13
            #PyQt5==5.11.3
            ...

5. Install PyQt5 from source. (This step no longer seems to be required to run plover headless on dietpi. Leaving info up for now.)
    * Note, this is a multi-hour process on the low powered raspberry pi zero

          >wget https://www.riverbankcomputing.com/static/Downloads/sip/sip-5.5.1.dev2011271026.tar.gz
          >wget https://www.riverbankcomputing.com/static/Downloads/PyQt5/PyQt5-5.15.3.dev2012241233.tar.gz
          >tar -zxvf sip...
          >tar -zxvf PyQt5...

          >cd sipsip-5.5.1.dev2011271026
          >sudo python3 setup.py build
          >sudo python3 setup.py install
          >cd ..

          >cd PyQt5-5.15.3.dev2012241233
          >sudo python3 configure.py
          >sudo make
          >sudo make install

5. Install Plover and plover-plugins
        
        >pip3 install --user -r requirements.txt
        >pip3 install --user -e . -r requirements_plugins.txt --no-build-isolation

6. Install and enable stenogotchi_link plugin for Plover 
     
        >plover -s plover_plugins install ./plover_plugin/
        >echo 'enabled_extensions = ["stenogotchi_link"]' >> ~/.config/plover/plover.cfg

7. Clone the Stenogotchi repository

        >cd ~ 
        >git clone https://github.com/Anodynous/stenogotchi.git
        >cd stenogotchi

8. Install and enable the stenogotchi_link plover plugin

        >/root/.local/bin/plover -s plover_plugins install ./plover_plugin/
        >echo 'enabled_extensions = ["stenogotchi_link"]' >> ~/.config/plover/plover.cfg

9. Install Stenogotchi dependencies

10. Configure Plover and Stenogotchi to start at boot.
    * Using dietpi-config enable automatic login of root to the local terminal
    * Automatically start the Stenogotchi and X server at boot

          >nano ~/.bash_profile
    
            if [[ -z $DISPLAY ]] && [[ $(tty) = /dev/tty1 ]]; then
              screen -S stenogotchi -dm python3 /root/stenogotchi/stenogotchi.py --debug
              xinit
            fi

    * Start Plover automatically at launch of X server

          >nano ~/.xinitrc
          
            screen -S plover /root/.local/bin/plover -l debug -g none

11. Add the below along with suitable configuration for your keyboard/machine in /root/.config/plover/plover.cfg

        [Machine Configuration]
        auto_start = True

12. Configure Stenogotchi and reboot

## Configuration
- Configuration files are placed in /etc/stenogotchi/
- Create a file called config.toml with overrides to the defaults. Don't edit default.toml directly as it is overridden on version updates

## Usage
![stenogotchi_2](https://user-images.githubusercontent.com/17461433/107883149-d5539680-6ef5-11eb-86fe-41f0b6293eed.jpg)

## Project roadmap
- [x] Proof of concept. Headless RPI0W running Plover, emulating bluetooth HID device and seamlessly piping steno output over BT to host
- [x] Create proper plugin for integration with Plover
- [x] Integrate bluetooth HID server as Stenogotchi plugin
- [x] Support for eINK display and web UI
- [x] Support for buttons for built-in and user customizable actions
- [x] Support for external battery charge readings on UI
- [x] Create Stenogotchi plugin to capture QWERTY input while blocking Plover
- [x] ButtonSHIM toggle to enable/disable WIFI
- [x] ButtonSHIM toggle between STENO and QWERTY output mode
- [x] WPM readings for STENO mode:
- [ ] Improved installation guide for Plover and Stenogotchi using DietPi as base image
- [ ] Clean up code, fix bugs and add test suite
- [ ] On-the-fly updating and reloading of plover dictionaries
- [ ] Dictionary lookup using eINK screen
- [ ] Improved web-ui, including emulation of the buttonSHIM
- [ ] Simple AI for shaping personality of the Stenogotchi
- [ ] Proper usage and configuration documentation
- [ ] Support for other eINK display modules
- [ ] Add launch option for barebones version. Intended to run on RPI0w without additional modules.

## Pictures
![stenogotchi_3](https://user-images.githubusercontent.com/17461433/107877063-cb6c6c00-6ed2-11eb-9f92-9059acd9f66d.jpeg)
![stenogotchi_4](https://user-images.githubusercontent.com/17461433/107876793-e3db8700-6ed0-11eb-83bb-648b08d1a315.jpeg)
![stenogotchi_5](https://user-images.githubusercontent.com/17461433/107876790-e0480000-6ed0-11eb-820d-65188cd0a031.jpeg)

## License
Released under the GPL3 license.