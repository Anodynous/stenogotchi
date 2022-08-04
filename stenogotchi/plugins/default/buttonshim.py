# ###############################################################
# Updated 20-03-2021 by Anodynous
# - Moved all functionality into class to remove dependency on global variables and improve integration with other plugins and core Stenogotchi functionality.
#
# Updated 13-01-2021 by Anodynous
# - Added support for hold action in addition to press.
#   Based on: https://github.com/evilsocket/pwnagotchi-plugins-contrib/blob/master/buttonshim.py
#       which in turn is based on https://github.com/pimoroni/button-shim/commit/143f35b4b56626bd7062bdff3245658af19822b4
#
################################################################


import logging
import RPi.GPIO as GPIO
import subprocess
import signal
import smbus
import time
from threading import Thread
import atexit
from colorsys import hsv_to_rgb

import stenogotchi
import stenogotchi.plugins as plugins

try:
    import queue
except ImportError:
    import Queue as queue

ADDR = 0x3f
LED_DATA = 7
LED_CLOCK = 6
REG_INPUT = 0x00
REG_OUTPUT = 0x01
REG_POLARITY = 0x02
REG_CONFIG = 0x03

NUM_BUTTONS = 5
BUTTON_A = 0
"""Button A"""
BUTTON_B = 1
"""Button B"""
BUTTON_C = 2
"""Button C"""
BUTTON_D = 3
"""Button D"""
BUTTON_E = 4
"""Button E"""
NAMES = ['A', 'B', 'C', 'D', 'E']
"""Sometimes you want to print the plain text name of the button that's triggered.
You can use::
    buttonshim.NAMES[button_index]
To accomplish this.
"""

ERROR_LIMIT = 10
FPS = 60
LED_GAMMA = [
    0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
    0, 0, 0, 0, 0, 0, 1, 1, 1, 1, 1, 1, 1, 2, 2, 2,
    2, 2, 2, 3, 3, 3, 3, 3, 4, 4, 4, 4, 5, 5, 5, 5,
    6, 6, 6, 7, 7, 7, 8, 8, 8, 9, 9, 9, 10, 10, 11, 11,
    11, 12, 12, 13, 13, 13, 14, 14, 15, 15, 16, 16, 17, 17, 18, 18,
    19, 19, 20, 21, 21, 22, 22, 23, 23, 24, 25, 25, 26, 27, 27, 28,
    29, 29, 30, 31, 31, 32, 33, 34, 34, 35, 36, 37, 37, 38, 39, 40,
    40, 41, 42, 43, 44, 45, 46, 46, 47, 48, 49, 50, 51, 52, 53, 54,
    55, 56, 57, 58, 59, 60, 61, 62, 63, 64, 65, 66, 67, 68, 69, 70,
    71, 72, 73, 74, 76, 77, 78, 79, 80, 81, 83, 84, 85, 86, 88, 89,
    90, 91, 93, 94, 95, 96, 98, 99, 100, 102, 103, 104, 106, 107, 109, 110,
    111, 113, 114, 116, 117, 119, 120, 121, 123, 124, 126, 128, 129, 131, 132, 134,
    135, 137, 138, 140, 142, 143, 145, 146, 148, 150, 151, 153, 155, 157, 158, 160,
    162, 163, 165, 167, 169, 170, 172, 174, 176, 178, 179, 181, 183, 185, 187, 189,
    191, 193, 194, 196, 198, 200, 202, 204, 206, 208, 210, 212, 214, 216, 218, 220,
    222, 224, 227, 229, 231, 233, 235, 237, 239, 241, 244, 246, 248, 250, 252, 255]

# The LED is an APA102 driven via the i2c IO expander.
# We must set and clear the Clock and Data pins
# Each byte in self._reg_queue represents a snapshot of the pin state


class Handler():
    plugin = None
    def __init__(self, plugin):
        self.press = None
        self.release = None

        self.hold = None
        self.hold_time = 0

        self.repeat = False
        self.repeat_time = 0

        self.t_pressed = 0
        self.t_repeat = 0
        self.hold_fired = False
        self.plugin = plugin


class Buttonshim(plugins.Plugin):
    __author__ = 'gon@o2online.de, Anodynous'
    __version__ = '0.0.2'
    __license__ = 'GPL3'
    __description__ = 'Pimoroni Button Shim GPIO Button and RGB LED support plugin based on the pimoroni-buttonshim-lib and the pwnagotchi-gpio-buttons-plugin'

    def __init__(self):
        self._agent = None
        self.running = False
        self.options = dict()
        self._running = False
        self._plover_wpm_meters_enabled = False
        
        self._states = None
        self._bus = None
        self._reg_queue = []
        self._update_queue = []
        self._brightness = 0.5
        self._led_queue = queue.Queue()
        self._t_poll = None
        self._running = False
        self._states = 0b00011111
        self._handlers = [None,None,None,None,None]
        self._button_was_held = False

    def on_loaded(self):
        logging.info("[buttonshim] GPIO Button plugin loaded.")
        self.running = True
        self._handlers = [Handler(self) for x in range(NUM_BUTTONS)]
        self.on_press([BUTTON_A, BUTTON_B, BUTTON_C, BUTTON_D, BUTTON_E], self.press_handler)
        self.on_hold([BUTTON_A, BUTTON_B, BUTTON_C, BUTTON_D, BUTTON_E], self.hold_handler)
        self.on_release([BUTTON_A, BUTTON_B, BUTTON_C, BUTTON_D, BUTTON_E], self.release_handler)

    def on_config_changed(self, config):
        self.config = config

    def on_ready(self, agent):
        self._agent = agent

    def set_ui_update(self, key, value):
        self._agent.view().set(key, value)

    def trigger_ui_update(self):
        self._agent.view().update()

    def _run(self):
        self._running = True
        _last_states = 0b00011111
        _errors = 0

        while self._running:
            led_data = None

            try:
                led_data = self._led_queue.get(False)
                self._led_queue.task_done()

            except queue.Empty:
                pass

            try:
                if led_data:
                    for chunk in self._chunk(led_data, 32):
                        self._bus.write_i2c_block_data(ADDR, REG_OUTPUT, chunk)

                self._states = self._bus.read_byte_data(ADDR, REG_INPUT)

            except IOError:
                _errors += 1
                if _errors > ERROR_LIMIT:
                    self._running = False
                    raise IOError("More than {} IO errors have occurred!".format(ERROR_LIMIT))

            for x in range(NUM_BUTTONS):
                last = (_last_states >> x) & 1
                curr = (self._states >> x) & 1
                handler = self._handlers[x]

                # If last > curr then it's a transition from 1 to 0
                # since the buttons are active low, that's a press event
                if last > curr:
                    handler.t_pressed = time.time()
                    handler.hold_fired = False

                    if callable(handler.press):
                        handler.t_repeat = time.time()
                        Thread(target=handler.press, args=(x, True, handler.plugin)).start()

                    continue

                if last < curr and callable(handler.release):
                    Thread(target=handler.release, args=(x, False, handler.plugin)).start()
                    continue

                if curr == 0:
                    if callable(handler.hold) and not handler.hold_fired and (time.time() - handler.t_pressed) > handler.hold_time:
                        Thread(target=handler.hold, args=(x,)).start()
                        handler.hold_fired = True

                    if handler.repeat and callable(handler.press) and (time.time() - handler.t_repeat) > handler.repeat_time:
                        self._handlers[x].t_repeat = time.time()
                        Thread(target=self._handlers[x].press, args=(x, True, handler.plugin)).start()

            _last_states = self._states

            time.sleep(1.0 / FPS)


    def _quit(self):

        if self._running:
            self._led_queue.join()
            self.set_pixel(0, 0, 0)
            self._led_queue.join()

        self._running = False
        self._t_poll.join()


    def setup(self):
        if self._bus is not None:
            return

        try:
            self._bus = smbus.SMBus(1)

            self._bus.write_byte_data(ADDR, REG_CONFIG, 0b00011111)
            self._bus.write_byte_data(ADDR, REG_POLARITY, 0b00000000)
            self._bus.write_byte_data(ADDR, REG_OUTPUT, 0b00000000)

            self._t_poll = Thread(target=self._run)
            self._t_poll.daemon = True
            self._t_poll.start()

            self.set_pixel(0, 0, 0)

            atexit.register(self._quit)
        except OSError as ex:
            logging.error(f"[buttonshim] Ignore if no ButtonSHIM hw module present and web UI enabled: OSError encountered during setup: {ex}")


    def _set_bit(self, pin, value):
        if value:
            self._reg_queue[-1] |= (1 << pin)
        else:
            self._reg_queue[-1] &= ~(1 << pin)


    def _next(self):
        if len(self._reg_queue) == 0:
            self._reg_queue = [0b00000000]
        else:
            self._reg_queue.append(self._reg_queue[-1])


    def _enqueue(self):
        self._led_queue.put(self._reg_queue)

        self._reg_queue = []


    def _chunk(self, l, n):
        for i in range(0, len(l)+1, n):
            yield l[i:i + n]


    def _write_byte(self, byte):
        for i in range(8):
            self._next()
            self._set_bit(LED_CLOCK, 0)
            self._set_bit(LED_DATA, byte & 0b10000000)
            self._next()
            self._set_bit(LED_CLOCK, 1)
            byte <<= 1


    def on_hold(self, buttons, handler=None, hold_time=1):
        """Attach a hold handler to one or more buttons.

        This handler is fired when you hold a button for hold_time seconds.

        When fired it will run in its own Thread.

        It will be passed one argument, the button index::

            @buttonshim.on_hold(buttonshim.BUTTON_A)
            def handler(button):
                # Your code here

        :param buttons: A single button, or a list of buttons
        :param handler: Optional: a function to bind as the handler
        :param hold_time: Optional: the hold time in seconds (default 2)

        """
        self.setup()

        if buttons is None:
            buttons = [BUTTON_A, BUTTON_B, BUTTON_C, BUTTON_D, BUTTON_E]

        if isinstance(buttons, int):
            buttons = [buttons]

        def attach_handler(handler):
            for button in buttons:
                self._handlers[button].hold = handler
                self._handlers[button].hold_time = hold_time

        if handler is not None:
            attach_handler(handler)
        else:
            return attach_handler


    def on_press(self, buttons, handler=None, repeat=False, repeat_time=0.5):
        """Attach a press handler to one or more buttons.

        This handler is fired when you press a button.

        When fired it will be run in its own Thread.

        It will be passed two arguments, the button index and a
        boolean indicating whether the button has been pressed/released::

            @buttonshim.on_press(buttonshim.BUTTON_A)
            def handler(button, pressed):
                # Your code here

        :param buttons: A single button, or a list of buttons
        :param handler: Optional: a function to bind as the handler
        :param repeat: Optional: Repeat the handler if the button is held
        :param repeat_time: Optional: Time, in seconds, after which to repeat

        """
        self.setup()

        if buttons is None:
            buttons = [BUTTON_A, BUTTON_B, BUTTON_C, BUTTON_D, BUTTON_E]

        if isinstance(buttons, int):
            buttons = [buttons]

        def attach_handler(handler):
            for button in buttons:
                self._handlers[button].press = handler
                self._handlers[button].repeat = repeat
                self._handlers[button].repeat_time = repeat_time

        if handler is not None:
            attach_handler(handler)
        else:
            return attach_handler


    def on_release(self, buttons=None, handler=None):
        """Attach a release handler to one or more buttons.

        This handler is fired when you let go of a button.

        When fired it will be run in its own Thread.

        It will be passed two arguments, the button index and a
        boolean indicating whether the button has been pressed/released::

            @buttonshim.on_release(buttonshim.BUTTON_A)
            def handler(button, pressed):
                # Your code here

        :param buttons: A single button, or a list of buttons
        :param handler: Optional: a function to bind as the handler

        """
        self.setup()

        if buttons is None:
            buttons = [BUTTON_A, BUTTON_B, BUTTON_C, BUTTON_D, BUTTON_E]

        if isinstance(buttons, int):
            buttons = [buttons]

        def attach_handler(handler):
            for button in buttons:
                self._handlers[button].release = handler

        if handler is not None:
            attach_handler(handler)
        else:
            return attach_handler


    def set_brightness(self, brightness):
        self.setup()

        if not isinstance(brightness, int) and not isinstance(brightness, float):
            raise ValueError("Brightness should be an int or float")

        if brightness < 0.0 or brightness > 1.0:
            raise ValueError("Brightness should be between 0.0 and 1.0")

        self._brightness = brightness


    def set_pixel(self, r, g, b):
        """Set the Button SHIM RGB pixel

        Display an RGB colour on the Button SHIM pixel.

        :param r: Amount of red, from 0 to 255
        :param g: Amount of green, from 0 to 255
        :param b: Amount of blue, from 0 to 255

        You can use HTML colours directly with hexadecimal notation in Python. EG::

            buttonshim.self.set_pixel(0xFF, 0x00, 0xFF)

        """
        self.setup()

        if not isinstance(r, int) or r < 0 or r > 255:
            raise ValueError("Argument r should be an int from 0 to 255")

        if not isinstance(g, int) or g < 0 or g > 255:
            raise ValueError("Argument g should be an int from 0 to 255")

        if not isinstance(b, int) or b < 0 or b > 255:
            raise ValueError("Argument b should be an int from 0 to 255")

        r, g, b = [int(x * self._brightness) for x in (r, g, b)]

        self._write_byte(0)
        self._write_byte(0)
        self._write_byte(0b11101111)
        self._write_byte(LED_GAMMA[b & 0xff])
        self._write_byte(LED_GAMMA[g & 0xff])
        self._write_byte(LED_GAMMA[r & 0xff])
        self._write_byte(0)
        self._write_byte(0)
        self._enqueue()

    def blink(self, r, g, b, ontime, offtime, blinktimes):
        logging.debug("[buttonshim] Blink")
        for i in range(0, blinktimes):
            self.set_pixel(r, g, b)
            time.sleep(ontime)
            self.set_pixel(0, 0, 0)
            time.sleep(offtime)

    def press_handler(self, button, pressed, plugin):
        """ On press reset button held status """
        self._button_was_held = False

    def reset_plover(self):
        command = {'reset_plover': True}
        plugins.loaded['plover_link'].send_signal_to_plover(command)
        logging.info(f"[buttonshim] Sent machine reset command to Plover")

    def toggle_qwerty_steno(self):
        try:
            cap_state = plugins.loaded['evdevkb'].get_capture_state()
            if not cap_state:
                plugins.loaded['evdevkb'].start_capture()
                logging.info(f"[buttonshim] Switched to QWERTY mode")
            else:
                plugins.loaded['evdevkb'].stop_capture()
                logging.info(f"[buttonshim] Switched to STENO mode")
        except Exception as ex:
            logging.exception(f"[buttonshim] Check if evdevkb is loaded, exception: {str(ex)}")
    
    def toggle_wpm_meters(self):
        command = {}
        try:
            wpm_method = plugins.loaded['plover_link'].options['wpm_method']
            wpm_timeout = plugins.loaded['plover_link'].options['wpm_timeout']
        except Exception as ex:
            logging.exception(f"[buttonshim] Check that wpm_method and wpm_timeout is configured. Falling back to defaults. Exception: {str(ex)}")
            wpm_method = 'ncra'
            wpm_timeout = '60'

        if self._plover_wpm_meters_enabled:
            command = {'stop_wpm_meter': 'wpm and strokes'}
            self.set_ui_update('wpm', '')
            self.set_ui_update('strokes', '')
            self.trigger_ui_update()
            logging.info(f"[buttonshim] Disabled WPM readings")

        elif not self._plover_wpm_meters_enabled:
            command = {'start_wpm_meter': 'wpm and strokes',
                        'wpm_method' : wpm_method,
                        'wpm_timeout' : wpm_timeout}

            self.set_ui_update('wpm', wpm_method)
            self.set_ui_update('strokes', f"{wpm_timeout}s")
            self.trigger_ui_update()

            logging.info(f"[buttonshim] Enabled WPM readings using method {wpm_method} and timeout {wpm_timeout}")

        self._plover_wpm_meters_enabled = not self._plover_wpm_meters_enabled
        plugins.loaded['plover_link'].send_signal_to_plover(command)
    
    def hold_handler(self, button):
        """ On long press run built in internal Stenogotchi commands """
        # Set button held status to prevent release_handler from triggering on release
        self._button_was_held = True

        # Blink in response to long hold event
        red = 0
        green = 70
        blue = 70
        on_time = 1
        off_time = 0
        blink_times = 1
        thread = Thread(target=self.blink, args=(red, green, blue, on_time, off_time, blink_times))
        thread.start()
           
        if NAMES[button] == 'A':
            # Toggle QWERTY/STENO mode
            self.toggle_qwerty_steno()     
        
        elif NAMES[button] == 'B':
            # Toggle WPM & strokes meters for Plover
            self.toggle_wpm_meters()

        elif NAMES[button] == 'C':
            # Triggers Plover machine reset
            self.reset_plover()

        elif NAMES[button] == 'D':
            # Toggle wifi on/off
            stenogotchi.set_wifi_onoff()
            # Check for changes in wifi status over a short while
            for i in range(5):
                self._agent._update_wifi()
                time.sleep(2)
            logging.info(f"[buttonshim] Toggled wifi state")
            
        elif NAMES[button] == 'E':
            # Initiate clean shutdown process
            logging.info(f"[buttonshim] Initiated clean shutdown")
            stenogotchi.shutdown()
    
    def release_handler(self, button, pressed, plugin):
        """ On short press run command from config """
        if not self._button_was_held:
            logging.info(f"[buttonshim] Button Pressed! Loading command from slot '{button}' for button '{NAMES[button]}'")
            bCfg = plugin.options['buttons'][NAMES[button]]
            blinkCfg = bCfg['blink']
            logging.debug(f'[buttonshim] {self.blink}')
            if blinkCfg['enabled'] == True:
                logging.debug(f"[buttonshim] Blinking led")
                red = int(blinkCfg['red'])
                green = int(blinkCfg['green'])
                blue = int(blinkCfg['blue'])
                on_time = float(blinkCfg['on_time'])
                off_time = float(blinkCfg['off_time'])
                blink_times =  int(blinkCfg['blink_times'])
                logging.debug(f"[buttonshim] red {red} green {green} blue {blue} on_time {on_time} off_time {off_time} blink_times {blink_times}")
                thread = Thread(target=self.blink, args=(red, green, blue, on_time, off_time, blink_times))
                thread.start()
                logging.debug(f"[buttonshim] Blink thread started")
            command = bCfg['command']
            if command == '':
                logging.debug(f"[buttonshim] Command empty")
            else:
                logging.debug(f"[buttonshim] Process create: {command}")
                process = subprocess.Popen(command, shell=True, stdin=None, stdout=open("/dev/null", "w"), stderr=None, executable="/bin/bash")
                process.wait()
                process = None
                logging.debug(f"[buttonshim] Process end")
