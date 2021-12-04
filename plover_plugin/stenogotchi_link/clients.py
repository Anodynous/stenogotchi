#!/usr/bin/env python3

import plover.log
import dbus, dbus.exceptions
from dbus.mainloop.glib import DBusGMainLoop

from time import sleep
from threading import Thread
from gi.repository import GLib

from plover.oslayer.xkeyboardcontrol import KeyboardEmulation, uchr_to_keysym, is_latin1, UCS_TO_KEYSYM
from plover import key_combo as plover_key_combo
from stenogotchi_link.keymap import plover_convert, plover_modkey

SERVER_DBUS = 'com.github.stenogotchi'
SERVER_SRVC = '/com/github/stenogotchi'
ERROR_NO_SERVER: str = 'A server is not currently running'
ERROR_SERVER_RUNNING: str = 'A server is already running'
TIME_SLEEP = 0


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
            plover.log.error(f'[stenogotchi_link] Failed to initialize D-Bus object: {str(e)}')
    
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

    def send_backspaces(self, y):
        self.stenogotchi_service.send_backspaces_stenogotchi(y)

    def send_string(self, s):
        self.stenogotchi_service.send_string_stenogotchi(s)

    def send_key_combination(self, s):
        self.stenogotchi_service.send_key_combination_stenogotchi(s)

    def send_lookup_results(self, l):
        self.stenogotchi_service.plover_translation_handler(l)

    def stenogotchi_signal_handler(self, dict):
        # Enable and disable wpm/strokes meters
        if 'lookup_word' in dict:
            self._engineserver.lookup_word(dict['lookup_word'])
        if 'lookup_stroke' in dict:
            self._engineserver.lookup_stroke(dict['lookup_stroke'])
        if 'output_to_stenogotchi' in dict:
            self._engineserver._output_to_stenogotchi = dict['output_to_stenogotchi']
        if 'start_wpm_meter' in dict:
            wpm_method = dict['wpm_method']
            wpm_timeout = int(dict['wpm_timeout'])
            plover.log.info('[stenogotchi_link] Starting WPM meter')
            if dict['start_wpm_meter'] == 'wpm and strokes':
                self._engineserver.start_wpm_meter(enable_wpm=True, enable_strokes=True, wpm_method=wpm_method, wpm_timeout=wpm_timeout)
            elif dict['start_wpm_meter'] == 'wpm':
                self._engineserver.start_wpm_meter(enable_wpm=True, enable_strokes=False, wpm_method=wpm_method, wpm_timeout=wpm_timeout)
            elif dict['start_wpm_meter'] == 'strokes':
                self._engineserver.start_wpm_meter(enable_wpm=False, enable_strokes=True, wpm_method=wpm_method, wpm_timeout=wpm_timeout)
        if 'stop_wpm_meter' in dict:
            plover.log.info('[stenogotchi_link] Stopping WPM meter')
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
        if norm_key < 0:    # Log for debug purposes in case keycode isn't valid
            plover.log.error(f"[stenogotchi_link] KeyError in update_keys, unable to send keycode: {norm_key}")
            return
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

    def send_keys(self, state_list=None):
        if not state_list:
            self.btk_service.send_keys([state_list])
        else:
            flat_list = state_list
            self.btk_service.send_keys(flat_list)

    def send_backspaces(self, number_of_backspaces):
        self.clear_keys()
        self.clear_mod_keys()
        state_list = []
        for x in range(number_of_backspaces):
            self.update_keys(42, 1)     # 42 is HID keycode for backspace
            state_list.append(self.state)
            self.update_keys(42, 0)
            state_list.append(self.state)
        self.send_keys(state_list)
        

    def map_hid_events(self, keycode, modifiers=None):
        """ Returns a list of HID bytearrays to produce the key combination.
        
        Arguments:
        keycode -- An integer in the inclusive range [8-255].
        modifiers -- An 8-bit bit mask indicating if the key
        pressed is modified by other keys, such as Shift, Capslock,
        Control, and Alt.
        TODO: International, accented characters and a range of symbols are not working with the US keyboard layout. 
            Could be solved using Alt codes on Windows, but Mac/iOS uses different Option codes. Complicated to solve 
            in a clean way as we only emulate a BT keyboard and all characters must be produced on the remote host.
            -> Look into separate WIN/MAC translation tables. Profiles which can be linked to BT MAC adresses.
        """
        self.clear_keys()
        self.clear_mod_keys()
        state_sublist = []
        #modifiers_list = [
        #    self.ke.modifier_mapping[n][0]
        #    for n in range(8)
        #    if (modifiers & (1 << n))
        #]
        #for mod_keycode in modifiers_list:
        #    self.update_mod_keys(plover_modkey(mod_keycode), 1)
             
        normkey_hid = plover_convert(keycode)
        # Log issues with mapping any keycodes
        if normkey_hid < 0:
            plover.log.error(f"[stenogotchi_link] Unable to map keycode: {keycode} using plover_convert in keymap.py.")
            return
        if modifiers:
            modkey_hid = plover_modkey(modifiers)
            if modkey_hid < 0:
                plover.log.error(f"[stenogotchi_link] Unable to map keycode: {keycode} using plover_modkey in keymap.py.")

        # Apply modifiers
        if modifiers:
            self.update_mod_keys(modkey_hid, 1)
        # Press and release the base key.
        self.update_keys(normkey_hid, 1)
        state_sublist.append(self.state)
        sleep(TIME_SLEEP)
        self.update_keys(normkey_hid, 0)
        state_sublist.append(self.state)
        # Release modifiers
        if modifiers > 0:
            self.update_mod_keys(modkey_hid, 0)
            state_sublist.append(self.state)
        
        return state_sublist
        #for mod_keycode in reversed(modifiers_list):
        #    self.update_mod_keys(plover_modkey(mod_keycode), 0)
        
    
    def send_string(self, s):
        # TODO: Universal handling for special cases
        state_list = []
        special_cases = ['<', '(', ')']
        for char in s:
            if char in special_cases:
                #plover.log.debug(f"[stenogotchi_link] handling special case character: {char}")
                if char == '<':
                    self.map_hid_events(59,50) # shift(,)
                elif char == '(':
                    self.map_hid_events(18,50) # shift(9)
                elif char == ')':
                    self.map_hid_events(19,50) # shift(0)
            keysym = uchr_to_keysym(char)
            mapping = self.ke._get_mapping(keysym)
            if mapping is None:
                continue
            sublist = self.map_hid_events(mapping.keycode, mapping.modifiers)
            if sublist:
                state_list.extend(sublist)
        if len(state_list) > 0:
            self.send_keys(state_list)
        
    def send_key_combination(self, combo_string: str):
        """
        Custom implementation of Plover send_key_combination function
        since we do not work with emulated key events or need to fight
        with a KeyboardCapture instance. 
        
        Arguments:

        combo_string -- A string representing a sequence of key
        combinations. Keys are represented by their names in the
        Xlib.XK module, without the 'XK_' prefix. For example, the
        left Alt key is represented by 'Alt_L'. Keys are either
        separated by a space or a left or right parenthesis.
        Parentheses must be properly formed in pairs and may be
        nested. A key immediately followed by a parenthetical
        indicates that the key is pressed down while all keys enclosed
        in the parenthetical are pressed and released in turn. For
        example, Alt_L(Tab) means to hold the left Alt key down, press
        and release the Tab key, and then release the left Alt key.
        """
        self.clear_keys()
        self.clear_mod_keys()
        state_list = []

        # Parse and validate combo.
        key_events = [
            (keycode, 1 if pressed else 0) for keycode, pressed
            in plover_key_combo.parse_key_combo(combo_string, self.ke._get_keycode_from_keystring)
        ]
       
        # Send key events to emulate combination.
        for keycode, event_type in key_events:
            # Convert to HID
            normkey_hid = plover_convert(keycode)
            modkey_hid = plover_modkey(keycode)

            # Update and send keycode if mapped, otherwise log
            if modkey_hid > -1:
                self.update_mod_keys(modkey_hid, event_type)
                state_list.append(self.state)
            elif normkey_hid > -1:
                self.update_keys(normkey_hid, event_type)
                state_list.append(self.state)
            else:
                plover.log.debug(f"[stenogotchi_link]Received key_combination from Plover: {combo_string}, resulting in key_events: {key_events}")
                plover.log.error(f"Unable to map keycode: {keycode}, in keymap.py (event_type: {event_type})")
        self.send_keys(state_list)
