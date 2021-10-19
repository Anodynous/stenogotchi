"""
Evdev based keyboard client for capturing input and relays the keypress to a Bluetooth HID keyboard emulator D-BUS Service

Based on: https://gist.github.com/ukBaz/a47e71e7b87fbc851b27cde7d1c0fcf0#file-readme-md
Which in turn takes the original idea from: http://yetanotherpointlesstechblog.blogspot.com/2016/04/emulating-bluetooth-keyboard-with.html

Tested on:
    Python 3.7 (needs 3.4+)
    Evdev 1.3.0
"""

import logging
import evdev
from select import select
from time import sleep

if not __name__ == '__main__':
    import stenogotchi.plugins as plugins
    ObjectClass = plugins.Plugin
else:
    import dbus
    ObjectClass = object

HID_DBUS = 'com.github.stenogotchi'
HID_SRVC = '/com/github/stenogotchi'

KEYTABLE = {
    "KEY_RESERVED": 0,
    "KEY_ESC": 41,
    "KEY_1": 30,
    "KEY_2": 31,
    "KEY_3": 32,
    "KEY_4": 33,
    "KEY_5": 34,
    "KEY_6": 35,
    "KEY_7": 36,
    "KEY_8": 37,
    "KEY_9": 38,
    "KEY_0": 39,
    "KEY_MINUS": 45,
    "KEY_EQUAL": 46,
    "KEY_BACKSPACE": 42,
    "KEY_TAB": 43,
    "KEY_Q": 20,
    "KEY_W": 26,
    "KEY_E": 8,
    "KEY_R": 21,
    "KEY_T": 23,
    "KEY_Y": 28,
    "KEY_U": 24,
    "KEY_I": 12,
    "KEY_O": 18,
    "KEY_P": 19,
    "KEY_LEFTBRACE": 47,
    "KEY_RIGHTBRACE": 48,
    "KEY_ENTER": 40,
    "KEY_LEFTCTRL": 224,
    "KEY_A": 4,
    "KEY_S": 22,
    "KEY_D": 7,
    "KEY_F": 9,
    "KEY_G": 10,
    "KEY_H": 11,
    "KEY_J": 13,
    "KEY_K": 14,
    "KEY_L": 15,
    "KEY_SEMICOLON": 51,
    "KEY_APOSTROPHE": 52,
    "KEY_GRAVE": 53,
    "KEY_LEFTSHIFT": 225,
    "KEY_BACKSLASH": 50,
    "KEY_Z": 29,
    "KEY_X": 27,
    "KEY_C": 6,
    "KEY_V": 25,
    "KEY_B": 5,
    "KEY_N": 17,
    "KEY_M": 16,
    "KEY_COMMA": 54,
    "KEY_DOT": 55,
    "KEY_SLASH": 56,
    "KEY_RIGHTSHIFT": 229,
    "KEY_KPASTERISK": 85,
    "KEY_LEFTALT": 226,
    "KEY_SPACE": 44,
    "KEY_CAPSLOCK": 57,
    "KEY_F1": 58,
    "KEY_F2": 59,
    "KEY_F3": 60,
    "KEY_F4": 61,
    "KEY_F5": 62,
    "KEY_F6": 63,
    "KEY_F7": 64,
    "KEY_F8": 65,
    "KEY_F9": 66,
    "KEY_F10": 67,
    "KEY_NUMLOCK": 83,
    "KEY_SCROLLLOCK": 71,
    "KEY_KP7": 95,
    "KEY_KP8": 96,
    "KEY_KP9": 97,
    "KEY_KPMINUS": 86,
    "KEY_KP4": 92,
    "KEY_KP5": 93,
    "KEY_KP6": 94,
    "KEY_KPPLUS": 87,
    "KEY_KP1": 89,
    "KEY_KP2": 90,
    "KEY_KP3": 91,
    "KEY_KP0": 98,
    "KEY_KPDOT": 99,
    "KEY_ZENKAKUHANKAKU": 148,
    "KEY_102ND": 100,
    "KEY_F11": 68,
    "KEY_F12": 69,
    "KEY_RO": 135,
    "KEY_KATAKANA": 146,
    "KEY_HIRAGANA": 147,
    "KEY_HENKAN": 138,
    "KEY_KATAKANAHIRAGANA": 136,
    "KEY_MUHENKAN": 139,
    "KEY_KPJPCOMMA": 140,
    "KEY_KPENTER": 88,
    "KEY_RIGHTCTRL": 228,
    "KEY_KPSLASH": 84,
    "KEY_SYSRQ": 70,
    "KEY_RIGHTALT": 230,
    "KEY_HOME": 74,
    "KEY_UP": 82,
    "KEY_PAGEUP": 75,
    "KEY_LEFT": 80,
    "KEY_RIGHT": 79,
    "KEY_END": 77,
    "KEY_DOWN": 81,
    "KEY_PAGEDOWN": 78,
    "KEY_INSERT": 73,
    "KEY_DELETE": 76,
    "KEY_MUTE": 239,
    "KEY_VOLUMEDOWN": 238,
    "KEY_VOLUMEUP": 237,
    "KEY_POWER": 102,
    "KEY_KPEQUAL": 103,
    "KEY_PAUSE": 72,
    "KEY_KPCOMMA": 133,
    "KEY_HANGEUL": 144,
    "KEY_HANJA": 145,
    "KEY_YEN": 137,
    "KEY_LEFTMETA": 227,
    "KEY_RIGHTMETA": 231,
    "KEY_COMPOSE": 101,
    "KEY_STOP": 243,
    "KEY_AGAIN": 121,
    "KEY_PROPS": 118,
    "KEY_UNDO": 122,
    "KEY_FRONT": 119,
    "KEY_COPY": 124,
    "KEY_OPEN": 116,
    "KEY_PASTE": 125,
    "KEY_FIND": 244,
    "KEY_CUT": 123,
    "KEY_HELP": 117,
    "KEY_CALC": 251,
    "KEY_SLEEP": 248,
    "KEY_WWW": 240,
    "KEY_COFFEE": 249,
    "KEY_BACK": 241,
    "KEY_FORWARD": 242,
    "KEY_EJECTCD": 236,
    "KEY_NEXTSONG": 235,
    "KEY_PLAYPAUSE": 232,
    "KEY_PREVIOUSSONG": 234,
    "KEY_STOPCD": 233,
    "KEY_REFRESH": 250,
    "KEY_EDIT": 247,
    "KEY_SCROLLUP": 245,
    "KEY_SCROLLDOWN": 246,
    "KEY_F13": 104,
    "KEY_F14": 105,
    "KEY_F15": 106,
    "KEY_F16": 107,
    "KEY_F17": 108,
    "KEY_F18": 109,
    "KEY_F19": 110,
    "KEY_F20": 111,
    "KEY_F21": 112,
    "KEY_F22": 113,
    "KEY_F23": 114,
    "KEY_F24": 115
}

# Map modifier keys to array element in the bit array
MODKEYS = {
    "KEY_RIGHTMETA": 0,
    "KEY_RIGHTALT": 1,
    "KEY_RIGHTSHIFT": 2,
    "KEY_RIGHTCTRL": 3,
    "KEY_LEFTMETA": 4,
    "KEY_LEFTALT": 5,
    "KEY_LEFTSHIFT": 6,
    "KEY_LEFTCTRL": 7
}

class EvdevKbrd:
    """
    Take the events from a physically attached keyboard and send the
    HID messages to the keyboard D-Bus server.
    """
    def __init__(self, skip_dbus = False):
        self._skip_dbus = skip_dbus
        self.do_capture = False
        self.keytable = KEYTABLE
        self.modkeys = MODKEYS
        self.target_length = 6
        self.mod_keys = 0b00000000
        self.pressed_keys = []
        self.have_kb = False
        self.devs = None
        if self._skip_dbus:
            self.bus = None
            self.btkobject = None
            self.btk_service = None
        else:
            self.bus = dbus.SystemBus()
            self.btkobject = self.bus.get_object(HID_DBUS, HID_SRVC)
            self.btk_service = dbus.Interface(self.btkobject, HID_DBUS)
        
    def convert(self, evdev_keycode):
        return self.keytable[evdev_keycode]

    def modkey(self, evdev_keycode):
        if evdev_keycode in self.modkeys:
            return self.modkeys[evdev_keycode]
        else:
            return -1  # Return an invalid array element
    
    def set_do_capture(self, toggle):
        self.do_capture = toggle

    def grab(self):
        # Make input device unavailable for other applications
        for dev in self.devs:
            dev.grab()

    def ungrab(self):
        # Release input device for other applications
        for dev in self.devs:
            dev.ungrab()
    
    def get_input_devices(self):
        # Returns all input devices connected to device
        input_devices = [evdev.InputDevice(path) for path in evdev.list_devices()]
        return input_devices

    def get_keyboards(self):
        # Returns all input devices that look like keyboards that are connected to device
        input_devices = self.get_input_devices()
        keyboards = []
        for device in input_devices:
            # Check if the input device has a KEY_A
            has_key_a = evdev.ecodes.KEY_A in device.capabilities().get(evdev.ecodes.EV_KEY, [])
            if has_key_a:
                keyboards.append(device)
                logging.debug(f"[evdevkb] Found keyboard '{device.name}' at path '{device.path}'")
        return keyboards
    
    def set_keyboards(self):
        # Sets all keyboards as device to listen for key-inputs from
        while not self.have_kb:
            if not self.do_capture:
                break
            keyboards = self.get_keyboards()
            if keyboards:
                self.devs = keyboards
                self.have_kb = True
            else:
                logging.debug('[evdevkb] Keyboard not found, waiting 3 seconds and retrying')
                sleep(3)

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
        property with the HID message to send for the current keys pressed
        on the keyboards
        :return: bytes of HID message
        """
        return [0xA1, 0x01, self.mod_keys, 0, *self.pressed_keys]

    def send_keys(self):
        # If ran as part of Stenogotchi, communicate directly with plugin
        if self._skip_dbus:
            plugins.loaded['plover_link']._stenogotchiservice.send_keys([self.state])
        # If ran as stand-alone, assume dbus is needed to access send_keys() function
        else:
            self.btk_service.send_keys(self.state)

    def event_loop(self):
        """
        Reads keypresses from all identified keyboards and sends them to emulated 
        bluetooth HID as long as do_capture is True.
        """
        self.do_capture = True
        self.grab()
        
        while self.do_capture:
            r, w, x = select(self.devs, [], [], 0.01)  # 0.1 is default
            for fd in r:
                for event in fd.read():
                    # We only want up/down key-events
                    if event.type == evdev.ecodes.EV_KEY and event.value < 2:
                        key_str = evdev.ecodes.KEY[event.code]
                        mod_key = self.modkey(key_str)
                        if mod_key > -1:
                            self.update_mod_keys(mod_key, event.value)
                        else:
                            self.update_keys(self.convert(key_str), event.value)
                        self.send_keys()
        self.ungrab()
        for dev in self.devs:
            dev.close()


class EvdevKeyboard(ObjectClass):
    __autohor__ = 'Anodynous'
    __version__ = '0.2'
    __license__ = 'MIT'
    __description__ = 'This plugin captures and blocks keypress events using evdev and sends to module emulating bluetooth HID device.'

    def __init__(self):
        self._agent = None
        self.evdevkb = None
        self.do_capture = False
     
    def on_ready(self, agent):
        self._agent = agent
        self.start_capture()

    def on_config_changed(self, config):
        self.config = config

    def trigger_ui_update(self, input_mode):
        self._agent.view().set('mode', input_mode)
        self._agent.view().update()

    def start_capture(self):
        logging.info('[evdevkb] Capturing evdev keypress events...')
        self.trigger_ui_update('READY')
        self.evdevkb = EvdevKbrd(skip_dbus=True)
        self.evdevkb.set_do_capture(True)
        self.do_capture = True
        self.evdevkb.set_keyboards()
        self.evdevkb.event_loop()

    def stop_capture(self):
        logging.info('[evdevkb] Ignoring evdev keypress events...')
        self.evdevkb.set_do_capture(False)
        self.do_capture = False
        self.evdevkb = None
        self.trigger_ui_update('STENO')
    
    def get_capture_state(self):
        return self.do_capture

if __name__ == '__main__':
    try:
        print('Setting up keyboard')
        kb = EvdevKbrd()

        print('starting event loop')
        kb.set_keyboards()
        kb.event_loop()
    except RuntimeError: pass       # Handling for bug in evdev 1.3.0, see https://github.com/gvalkov/python-evdev/issues/120

