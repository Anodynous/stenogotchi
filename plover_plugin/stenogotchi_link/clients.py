#!/usr/bin/env python3


import logging
import dbus, dbus.exceptions
from dbus.mainloop.glib import DBusGMainLoop

from time import sleep
from threading import Thread
from gi.repository import GLib

from plover.oslayer.xkeyboardcontrol import KeyboardEmulation, uchr_to_keysym, is_latin1, UCS_TO_KEYSYM
from stenogotchi_link.keymap import plover_convert, plover_modkey

SERVER_DBUS = 'com.github.stenogotchi'
SERVER_SRVC = '/com/github/stenogotchi'
ERROR_NO_SERVER: str = 'A server is not currently running'
ERROR_SERVER_RUNNING: str = 'A server is already running'
TIME_SLEEP = 0.001


class StenogotchiClient:
    """ 
    Transmits Plover event updates to, and listens for signals from, Stenogotchi over D-Bus.
    """
    def __init__(self, engineserver):
        self._engineserver = engineserver
        self._setup_dbus_loop()
        self._setup_object()
    
    def _setup_dbus_loop(self):
        DBusGMainLoop(set_as_default=True)
        self._mainloop = GLib.MainLoop()
        self._thread = Thread(target=self._mainloop.run)
        self._thread.start()

    def _setup_object(self):
        try:
            self.bus = dbus.SystemBus()
            self.stenogotchiobject = self.bus.get_object(SERVER_DBUS, SERVER_SRVC)
            self.stenogotchi_service = dbus.Interface(self.stenogotchiobject, SERVER_DBUS)
        
            # Add signal receiver for incoming messages
            self.stenogotchi_signal = self.bus.add_signal_receiver(path=SERVER_SRVC,
                                                                handler_function=self.stenogotchi_signal_handler,
                                                                dbus_interface=SERVER_DBUS,
                                                                signal_name='signal_to_plover')
        except dbus.exceptions.DBusException as e:
            logging.error(f'[stenogotchi_link] Failed to initialize D-Bus object: {str(e)}')
    
    def _exit(self):
        self._mainloop.quit()

    def plover_is_running(self, b):
        self.stenogotchi_service.plover_is_running(b)
        # If plover is shutting down, quit mainloop
        if not b:
            self._exit()

    def plover_is_ready(self, b):
        self.stenogotchi_service.plover_is_ready(b)

    def plover_machine_state(self, s):
        self.stenogotchi_service.plover_machine_state(s)

    def plover_output_enabled(self, b):
        self.stenogotchi_service.plover_output_enabled(b)

    def plover_wpm_stats(self, s):
        self.stenogotchi_service.plover_wpm_stats(s)

    def plover_strokes_stats(self, s):
        self.stenogotchi_service.plover_strokes_stats(s)

    def stenogotchi_signal_handler(self, dict):
        # Enable and disable wpm/strokes meters
        if 'start_wpm_meter' in dict:
            wpm_method = dict['wpm_method']
            wpm_timeout = int(dict['wpm_timeout'])
            logging.info('[stenogotchi_link] Starting WPM meter')
            if dict['start_wpm_meter'] == 'wpm and strokes':
                self._engineserver.start_wpm_meter(enable_wpm=True, enable_strokes=True, wpm_method=wpm_method, wpm_timeout=wpm_timeout)
            elif dict['start_wpm_meter'] == 'wpm':
                self._engineserver.start_wpm_meter(enable_wpm=True, enable_strokes=False, wpm_method=wpm_method, wpm_timeout=wpm_timeout)
            elif dict['start_wpm_meter'] == 'strokes':
                self._engineserver.start_wpm_meter(enable_wpm=False, enable_strokes=True, wpm_method=wpm_method, wpm_timeout=wpm_timeout)
        if 'stop_wpm_meter' in dict:
            logging.info('[stenogotchi_link] Stopping WPM meter')
            if dict['stop_wpm_meter'] == 'wpm and strokes':
                self._engineserver.stop_wpm_meter(disable_wpm=True, disable_strokes=True)
            elif dict['stop_wpm_meter'] == 'wpm':
                self._engineserver.stop_wpm_meter(disable_wpm=True, disable_strokes=False)
            elif dict['stop_wpm_meter'] == 'strokes':
                self._engineserver.stop_wpm_meter(disable_wpm=False, disable_strokes=True)


class BTClient:
    """
    Transmits keystroke output from Plover to Stenogotchi as HID messages over D-Bus.
    """

    def __init__(self):
        self.target_length = 6
        self.mod_keys = 0b00000000
        self.pressed_keys = []
        self.bus = dbus.SystemBus()
        self.btkobject = self.bus.get_object(SERVER_DBUS, SERVER_SRVC)
        self.btk_service = dbus.Interface(self.btkobject, SERVER_DBUS)
        self.ke = KeyboardEmulation()


    def update_mod_keys(self, mod_key, value):
        """
        Which modifier keys are active is stored in an 8 bit number. 
        Each bit represents a different key. This method takes which bit
        and its new value as input
        :param mod_key: The value of the bit to be updated with new value
        :param value: Binary 1 or 0 depending if pressed or released
        """
        bit_mask = 1 << (7-mod_key)
        if value: # set bit
            self.mod_keys |= bit_mask
        else: # clear bit
            self.mod_keys &= ~bit_mask

    def update_keys(self, norm_key, value):
        """
        Sets the active normal keys
        """
        if value < 1:
            self.pressed_keys.remove(norm_key)
        elif norm_key not in self.pressed_keys:
            self.pressed_keys.insert(0, norm_key)
        len_delta = self.target_length - len(self.pressed_keys)
        if len_delta < 0:
            self.pressed_keys = self.pressed_keys[:len_delta]
        elif len_delta > 0:
            self.pressed_keys.extend([0] * len_delta)
    
    @property
    def state(self):
        """
        property with the HID message to be sent
        :return: bytes of HID message
        """
        return [0xA1, 0x01, self.mod_keys, 0, *self.pressed_keys]

    def clear_mod_keys(self):
        self.mod_keys = 0b00000000

    def clear_keys(self):
        self.pressed_keys = []

    def send_keys(self):
        self.btk_service.send_keys(self.state)

    def send_backspaces(self, number_of_backspaces):
        self.clear_keys()
        self.clear_mod_keys()
        for x in range(number_of_backspaces):
            self.update_keys(42, 1)     # 42 is HID keycode for backspace
            self.send_keys()
            sleep(TIME_SLEEP)
            self.update_keys(42, 0)
            self.send_keys()
            sleep(TIME_SLEEP)

    def send_plover_keycode(self, keycode, modifiers=0):
        #modifiers_list = [
        #    self.ke.modifier_mapping[n][0]
        #    for n in range(8)
        #    if (modifiers & (1 << n))
        #]
        if modifiers > 1:
            logging.debug("[stenogotchi_link] Modifier received: " + str(modifiers) +" keycode" + str(keycode))
        # Update modifier keys
        #for mod_keycode in modifiers_list:
        #    self.update_mod_keys(plover_modkey(mod_keycode), 1)
        if modifiers > 1:       # Should update this to handle multiple modifier keys like plover does
            self.update_mod_keys(plover_modkey(modifiers), 1)

        # Press and release the base key.
        self.update_keys(plover_convert(keycode), 1)
        self.send_keys()
        sleep(TIME_SLEEP)
        self.update_keys(plover_convert(keycode), 0)
        self.send_keys()
        # Release modifiers
        if modifiers == 1:
            self.update_mod_keys(plover_modkey(modifiers), 0)
        #for mod_keycode in reversed(modifiers_list):
        #    self.update_mod_keys(plover_modkey(mod_keycode), 0)
    
    def send_string(self, s):
        for char in s:
            keysym = uchr_to_keysym(char)
            mapping = self.ke._get_mapping(keysym)
            if mapping is None:
                continue
            self.send_plover_keycode(mapping.keycode,
                               mapping.modifiers)