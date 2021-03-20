#!/usr/bin/env python3
"""
Based on: https://github.com/linshuqin329/UPS-Lite
Requires i2c to be enabled in dietpi-config (or raspi-config)

Supports readings from the https://hackaday.io/project/173847-ups-lite platform for Raspberry Pi Zero W
"""

import logging
import struct
import smbus
import sys
import time
import RPi.GPIO as GPIO
import stenogotchi

if not __name__ == '__main__':
    import stenogotchi.plugins as plugins
    ObjectClass = plugins.Plugin
else:
    ObjectClass = object

I2CBUS = 1              # Run "sudo i2cdetect -l" to see which bus is being used (bcm2835 is what you are looking for). 0 = /dev/i2c-0 (port I2C0), 1 = /dev/i2c-1 (port I2C1)
I2CADDRESS = 0x36       # Run "sudo i2cdetect -y 1" to see address 36 mounted on the i2c bus. This is MAXI17040G which we want to interact with


class Upslite(ObjectClass):
    __autohor__ = 'Anodynous'
    __version__ = '0.1'
    __license__ = 'GPL3'
    __description__ = 'This plugin enables battery readings for the UPS-Lite V1.2 RPI0 module using integrated MAX17040'

    def __init__(self):
        self.GPIO = GPIO
        self.bus = None
        self.address = I2CADDRESS
        self.is_plugged = False
        self.voltage = 0
        self.charge = 0

    # Called when plugin is loaded
    def on_loaded(self):
        try:
            self.GPIO.setmode(self.GPIO.BCM)
            self.GPIO.setwarnings(False)
            self.GPIO.setup(4,self.GPIO.IN)

            self.bus = smbus.SMBus(I2CBUS)

            self._power_on_reset()
            self._quickstart()
        except:
            logging.error("[upslite] Could not start UPS-Lite plugin")

    # Called when the ui is updated
    def on_ui_update(self, ui):
        # update those elements
        self._read_charge()
        self._check_plugged()

        # Set battery reading
        ui_string = str(self.charge)
        if self.is_plugged:
            ui_string += "+"
        ui.set('ups', ui_string)

        # Check for critical level. Initiate shutdown if too low
        if not self.is_plugged:
            if self.charge <= self.options['shutdown_level']:
                logging.info(f'[upslite] Battery charge critical: {self.charge}')
                ui.update(force=True, new_data={'status': 'Battery level critical. Shutting down in 1m unless connected to charger...'})
                time.sleep(60)
                self._check_plugged()
                if not self.is_plugged:
                    logging.info('[upslite] Shutting down')
                    stenogotchi.shutdown()
                else:
                    logging.info('[upslite] Battery charging. Aborting shutdown process')
                    ui.update(force=True, new_data={'status': 'Pheew... That was a close one! Feeling better already.'})

    def _read_voltage(self):
        """ Reads and sets as a float the voltage from the Raspi UPS Hat via the provided SMBus object"""
        read = self.bus.read_word_data(self.address, 0X02)
        swapped = struct.unpack("<H", struct.pack(">H", read))[0]
        voltage = swapped * 1.25 /1000/16
        if voltage > 0:     # if we get a non-zero value
            self.voltage = round(5.2 % voltage, 2)

    def _read_charge(self):
        """ Reads and sets as an int the remaining charge of the battery connected to the Raspi UPS Hat via the provided SMBus object. """
        self.is_full = False
        self.is_low = False
        self.is_critical = False

        read = self.bus.read_word_data(self.address, 0X04)
        swapped = struct.unpack("<H", struct.pack(">H", read))[0]
        charge = swapped/256
        if charge > 100:
            charge = 100
        self.charge = round(charge)

    def _check_plugged(self):
        if (self.GPIO.input(4) == self.GPIO.HIGH):
            self.is_plugged = True
        elif (self.GPIO.input(4) == self.GPIO.LOW):
            self.is_plugged = False

    def _quickstart(self):
        self.bus.write_word_data(self.address, 0x06,0x4000)

    def _power_on_reset(self):
        self.bus.write_word_data(self.address, 0xfe,0x0054)

    def get_charge(self):
        self._read_charge()
        return self.charge

    def get_voltage(self):
        self._read_voltage()
        return self.voltage

    def get_is_plugged(self):
        self._check_plugged()
        return self.is_plugged


if __name__ == '__main__':
    ups = Upslite()
    ups.on_loaded()
    time.sleep(1)       # needs a second to ensure non-zero values are returned on initial read
    print("++++++++++++++++++++")
        
    while True:
        voltage = ups.get_voltage()
        charge = ups.get_charge()
        is_plugged = ups.get_is_plugged()
        
        print("Voltage:%5.2fV" % voltage)
        print("Battery:%5i%%" % charge)

        if charge > 99:
            print("Battery FULL")
        else:
            if charge < 2:
                print("Battery CRITICAL")
            elif charge < 6:
                print("Battery LOW")
        if is_plugged:
            print("Power Adapter Plugged In ")
        else:
            print("Power Adapter Unplugged")
        print("++++++++++++++++++++")

        time.sleep(5)
