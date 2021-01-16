# Stenogotchi
Aim of the project is to deliver a cheap, portable, stand-alone device for running [Plover](https://www.openstenoproject.org/ "Plover: Open Steno Project") where local installation on the host is impossible or simply not preferred. A link enabling stenographic input with any device supported by Plover on any device accepting bluetooth keyboards. 

Likely use-cases include: 
- Mobile devices
- Corporate and public computers restricting software installations 
- Hassle-free switching between devices without the need to re-install and configure Plover
- On-the-go stenographic recording without access to computer

Stenogotchi is based on the [pwnagotchi](https://github.com/evilsocket/pwnagotchi) code, but instead of hungering for WPA handshakes it feeds on your steno chords. It emulates a BT HID device for connecting to a host and output can be toggled between STENO and QWERTY mode on the fly. The friendly UI optimized for low-power eINK displays is also accessible as a web-ui version, making both the eINK display and buttonSHIM modules optional. If the RPI0w always will be powered over microUSB the battery pack is not needed.

## Hardware
| Module                                                                           | Status       |
|:---------------------------------------------------------------------------------|:-------------|
| [Raspberry Pi Zero W](https://www.raspberrypi.org/products/raspberry-pi-zero-w/) | Required     |
| [Waveshare 2.13 v.2](https://www.waveshare.com/wiki/2.13inch_e-Paper_HAT)        | Recommended  |
| [ButtonSHIM](https://shop.pimoroni.com/products/button-shim)                     | Recommended  |
| [UPS-Lite v1.2](https://hackaday.io/project/173847-ups-lite)                     | Optional     |

## Installation
1. Setup and DietPi image
2. Configure and install pre-requisites
3. Build PyQt5 from source
4. Install Plover
5. Install stenogotchi link plugin for Plover
    - `plover -s plover_plugins install ./plover_plugin/`
6. Install Stenogotchi

## Configuration

## Usage

## Project roadmap
- [x] POC: Headless RPI0W running Plover, emulating bluetooth HID device and seamlessly piping steno output over BT to host
- [x] Proper plugin for integration with Plover
- [x] Bluetooth HID emulation
- [x] Support for eINK display and web UI, [waveshare 2.13v2](https://www.waveshare.com/wiki/2.13inch_e-Paper_HAT)
- [x] Support for buttons for built-in and user customizable actions, [buttonSHIM](https://shop.pimoroni.com/products/button-shim)
- [x] Support for external battery charge reading on UI, [UPS-Lite v1.2](https://hackaday.io/project/173847-ups-lite)
- [x] Toggle to enable/disable WIFI
- [ ] Toggle between STENO and QWERTY output mode
- [ ] WPM readings for both STENO and QWERTY modes
- [ ] On-the-fly updating of plover dictionaries
- [ ] Local-only-mode (no bluetooth output, records output to microSD card)
- [ ] Improved web-ui, including emulation of the buttonSHIM
- [ ] Simple AI for shaping personality of the stenogotchi 
- [ ] Proper documentation
- [ ] Support for other display modules
- [ ] Fully automated build script for setting up Dietpi image with Plover and Stenogotchi installed and configured
- [ ] Separate barebones version. Only including Plover plugin and BT HID emulation for piping steno output

## Screenshots

## License
Released under the GPL3 license.