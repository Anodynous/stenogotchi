# ###############################################################
# Based on: https://github.com/evilsocket/pwnagotchi/blob/master/pwnagotchi/plugins/default/example.py
#
# Changed 22-03-2021 by Anodynous
# - Changed to fit Stenogotchi events
#
################################################################

import logging

import stenogotchi.plugins as plugins
from stenogotchi.ui.components import LabeledValue
from stenogotchi.ui.view import BLACK
import stenogotchi.ui.fonts as fonts


class Example(plugins.Plugin):
    __author__ = 'evilsocket@gmail.com, Anodynous'
    __version__ = '1.0.0'
    __license__ = 'GPL3'
    __description__ = 'An example plugin for pwnagotchi that implements all the available callbacks.'

    def __init__(self):
        logging.debug("[example] example plugin created")

    # called when http://<host>:<port>/plugins/<plugin>/ is called
    # must return a html page
    # IMPORTANT: If you use "POST"s, add a csrf-token (via csrf_token() and render_template_string)
    def on_webhook(self, path, request):
        logging.info("[example] webhook established")

    # called when the plugin is loaded
    def on_loaded(self):
        logging.warning("[example] WARNING: this plugin should be disabled! options = " % self.options)

    # called before the plugin is unloaded
    def on_unload(self, ui):
        logging.info("[example] is unloaded")

    # called hen there's internet connectivity
    def on_internet_available(self, agent):
        logging.info("[example] unit has internet connection")

    # called to setup the ui elements
    def on_ui_setup(self, ui):
        # add custom UI elements
        ui.add_element('ups', LabeledValue(color=BLACK, label='UPS', value='0%/0V', position=(ui.width() / 2 - 25, 0),
                                           label_font=fonts.Bold, text_font=fonts.Medium))

    # called when the ui is updated
    def on_ui_update(self, ui):
        # update those elements
        some_voltage = 0.1
        some_capacity = 100.0
        ui.set('ups', "%4.2fV/%2i%%" % (some_voltage, some_capacity))

    # called when the hardware display setup is done, display is an hardware specific object
    def on_display_setup(self, display):
        logging.info("[example] unit has set up display")

    # called when everything is ready and the main loop is about to start
    def on_ready(self, agent):
        logging.info("[example] unit is ready")
        # you can run custom bettercap commands if you want
        #   agent.run('ble.recon on')
        # or set a custom state
        #   agent.set_bored()

    # called when the status is set to grateful
    def on_grateful(self, agent):
        logging.info("[example] unit is grateful")

    # called when the status is set to lonely
    def on_lonely(self, agent):
        logging.info("[example] unit is lonely")

    # called when the status is set to bored
    def on_bored(self, agent):
        logging.info("[example] unit is bored")

    # called when the status is set to sad
    def on_sad(self, agent):
        logging.info("[example] unit is sad")

    # called when the status is set to angry
    def on_angry(self, agent):
        logging.info("[example] unit is angry")

    # called when the status is set to excited
    def on_excited(self, agent):
        logging.info("[example] unit is excited")

    # called when the agent is rebooting the board
    def on_rebooting(self, agent):
        logging.info("[example] unit is rebooting")

    # called when the agent is waiting for t seconds
    def on_wait(self, agent, t):
        logging.info(f"[example] unit is waiting {t} seconds")

    # called when the agent is sleeping for t seconds
    def on_sleep(self, agent, t):
        logging.info(f"[example] unit is sleeping {t} seconds")

    # called when an epoch is over (where an epoch is a single loop of the main algorithm)
    def on_epoch(self, agent, epoch, epoch_data):
        logging.info(f"[example] epoch is over")

    # called when successfully connected to a bluetooth host
    def on_bt_connected(self, agent, bthost_name):
        logging.info(f"[example] unit connected to bluetooth host '{bthost_name}'")

    # called when disconnected from bluetooth host
    def on_bt_disconnected(self, agent):
        logging.info("[example] unit disconnected from bluetooth host")

    # called when plover boots
    def on_plover_boot(self, agent):
        logging.info("[example] Plover is starting up")

    # called when plover is ready
    def on_plover_ready(self, agent):
        logging.info("[example] Plover is ready")

    # called when plover quits
    def on_plover_quit(self, agent):
        logging.info("[example] Plover has quit")

    # called when wifi is connected
    def on_wifi_connected(self, agent, ssid, ip):
        logging.info(f"[example] unit is connected to wifi '{ssid}' using ip '{ip}'")

    # called when wifi is disconnected
    def on_wifi_disconnected(self, agent):
        logging.info("[example] unit is disconnected from wifi")

    # called when wpm stats are updated
    def on_wpm_stats(self, agent):
        logging.info("[example] unit received new WPM stats")

    # called when wpm-strokes stats are updated
    def on_strokes_stats(self, agent):
        logging.info("[example] unit received new WPM-strokes stats")