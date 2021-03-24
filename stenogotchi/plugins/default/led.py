# ###############################################################
# Based on: https://github.com/evilsocket/pwnagotchi/blob/master/pwnagotchi/plugins/default/led.py
#
# Changed 22-03-2021 by Anodynous
# - Changed to fit Stenogotchi events
#
################################################################

from threading import Event
import _thread
import logging
import time

import stenogotchi.plugins as plugins


class Led(plugins.Plugin):
    __author__ = 'evilsocket@gmail.com, Anodynous'
    __version__ = '1.0.0'
    __license__ = 'GPL3'
    __description__ = 'This plugin blinks the PWR led with different patterns depending on the event.'

    def __init__(self):
        self._is_busy = False
        self._event = Event()
        self._event_name = None
        self._led_file = "/sys/class/leds/led0/brightness"
        self._delay = 200

    # called when the plugin is loaded
    def on_loaded(self):
        self._led_file = "/sys/class/leds/led%d/brightness" % self.options['led']
        self._delay = int(self.options['delay'])

        logging.info("[led] plugin loaded for %s" % self._led_file)
        self._on_event('loaded')
        _thread.start_new_thread(self._worker, ())

    def on_config_changed(self, config):
        self.config = config

    def _on_event(self, event):
        if not self._is_busy:
            self._event_name = event
            self._event.set()
            logging.debug("[led] event '%s' set", event)
        else:
            logging.debug("[led] skipping event '%s' because the worker is busy", event)

    def _led(self, on):
        with open(self._led_file, 'wt') as fp:
            fp.write(str(on))

    def _blink(self, pattern):
        logging.debug("[led] using pattern '%s' ..." % pattern)
        for c in pattern:
            if c == ' ':
                self._led(1)
            else:
                self._led(0)
            time.sleep(self._delay / 1000.0)
        # reset
        self._led(0)

    def _worker(self):
        while True:
            self._event.wait()
            self._event.clear()
            self._is_busy = True

            try:
                if self._event_name in self.options['patterns']:
                    pattern = self.options['patterns'][self._event_name]
                    self._blink(pattern)
                else:
                    logging.debug("[led] no pattern defined for %s" % self._event_name)
            except Exception as e:
                logging.exception("[led] error while blinking")

            finally:
                self._is_busy = False

    # called when the unit is updating its software
    def on_updating(self):
        self._on_event('updating')

    # called when there's internet connectivity
    def on_internet_available(self, agent):
        self._on_event('internet_available')

    # called when everything is ready and the main loop is about to start
    def on_ready(self, agent):
        self._on_event('ready')

    # called when the status is set to grateful
    def on_grateful(self, agent):
        self._on_event('grateful')

    # called when the status is set to lonely
    def on_lonely(self, agent):
        self._on_event('lonely')

    # called when the status is set to bored
    def on_bored(self, agent):
        self._on_event('bored')

    # called when the status is set to sad
    def on_sad(self, agent):
        self._on_event('sad')

    # called when the status is set to angry
    def on_angry(self, agent):
        self._on_event('angry')

    # called when the status is set to excited
    def on_excited(self, agent):
        self._on_event('excited')

    # called when the agent is rebooting the board
    def on_rebooting(self, agent):
        self._on_event('rebooting')

    # called when the agent is waiting for t seconds
    def on_wait(self, agent, t):
        self._on_event('wait')

    # called when the agent is sleeping for t seconds
    def on_sleep(self, agent, t):
        self._on_event('sleep')

    # called when an epoch is over (where an epoch is a single loop of the main algorithm)
    def on_epoch(self, agent, epoch, epoch_data):
        self._on_event('epoch')

    # called when successfully connected to a bluetooth host
    def on_bt_connected(self, agent, bthost_name):
        self._on_event('bt_connected')

    # called when disconnected from bluetooth host
    def on_bt_disconnected(self, agent):
        self._on_event('bt_disconnected')

    # called when plover boots
    def on_plover_boot(self, agent):
        self._on_event('plover_boot')

    # called when plover is ready
    def on_plover_ready(self, agent):
        self._on_event('plover_ready')

    # called when plover quits
    def on_plover_quit(self, agent):
        self._on_event('plover_quit')

    # called when wifi is connected
    def on_wifi_connected(self, agent, ssid, ip):
        self._on_event('wifi_connected')

    # called when wifi is disconnected
    def on_wifi_disconnected(self, agent):
        self._on_event('wifi_disconnected')

    # called when wpm stats are updated
    def on_wpm_stats(self, agent):
        self._on_event('wpm_set')

    # called when wpm-strokes stats are updated
    def on_strokes_stats(self, agent):
        self._on_event('strokes_set')