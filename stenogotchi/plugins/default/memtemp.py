# memtemp shows memory infos and cpu temperature
#
# mem usage, cpu load, cpu temp
#
###############################################################
#
# Updated 13-01-2021 by Anodynous
# - Changed CPU reading from using default method to having a 
#   continuously updating 60s average to draw upon. Default 
#   method returns 90-100% on RPI0 when triggered alongside 
#   an on_ui_update event 
#
# Updated 18-10-2019 by spees <speeskonijn@gmail.com>
# - Changed the place where the data was displayed on screen
# - Made the data a bit more compact and easier to read
# - removed the label so we wont waste screen space
# - Updated version to 1.0.1
#
# 20-10-2019 by spees <speeskonijn@gmail.com>
# - Refactored to use the already existing functions
# - Now only shows memory usage in percentage
# - Added CPU load
# - Added horizontal and vertical orientation
#
###############################################################
from stenogotchi.ui.components import LabeledValue
from stenogotchi.ui.view import BLACK
import stenogotchi.ui.fonts as fonts
import stenogotchi.plugins as plugins
import stenogotchi
import logging
import _thread


class MemTemp(plugins.Plugin):
    __author__ = 'https://github.com/xenDE'
    __version__ = '1.0.1'
    __license__ = 'GPL3'
    __description__ = 'A plugin that will display memory/cpu usage and temperature'

    def __init__(self):
        self.cpu_load_avg = 0

    def on_loaded(self):
        logging.info("[memtemp] memtemp plugin loaded.")
        _thread.start_new_thread(self._cpu_poller(), ())

    def on_config_changed(self, config):
        self.config = config

    def mem_usage(self):
        return int(stenogotchi.mem_usage() * 100)

    def cpu_load(self):
        #return int(stenogotchi.cpu_load() * 100)
        return int(self.cpu_load_avg * 100)


    def _cpu_poller(self, s=60):
        """
        Runs in own thread and continually recalculates the CPU load over a (s)-second long window
        """
        while True:
            self.cpu_load_avg = stenogotchi.cpu_load(s)

    def on_ui_setup(self, ui):
        if ui.is_waveshare_v2():
            h_pos = (180, 80)
            v_pos = (180, 61)
        elif ui.is_waveshare_v1():
            h_pos = (170, 80)
            v_pos = (170, 61)
        elif ui.is_waveshare144lcd():
            h_pos = (53, 77)
            v_pos = (78, 67)
        elif ui.is_inky():
            h_pos = (140, 68)
            v_pos = (165, 54)
        elif ui.is_waveshare27inch():
            h_pos = (192, 138)
            v_pos = (216, 122)
        else:
            h_pos = (155, 76)
            v_pos = (180, 61)

        if self.options['orientation'] == "vertical":
            ui.add_element('memtemp', LabeledValue(color=BLACK, label='', value=' mem:-\n cpu:-\ntemp:-',
                                                   position=v_pos,
                                                   label_font=fonts.Small, text_font=fonts.Small))
        else:
            # default to horizontal
            ui.add_element('memtemp', LabeledValue(color=BLACK, label='', value='mem cpu temp\n - -  -',
                                                   position=h_pos,
                                                   label_font=fonts.Small, text_font=fonts.Small))

    def on_unload(self, ui):
        with ui._lock:
            ui.remove_element('memtemp')

    def on_ui_update(self, ui):
        if self.options['scale'] == "fahrenheit":
            temp = (stenogotchi.temperature() * 9 / 5) + 32
            symbol = "f"
        elif self.options['scale'] == "kelvin":
            temp = stenogotchi.temperature() + 273.15
            symbol = "k"
        else:
            # default to celsius
            temp = stenogotchi.temperature()
            symbol = "c"

        if self.options['orientation'] == "vertical":
            ui.set('memtemp',
                   " mem:%s%%\n cpu:%s%%\ntemp:%s%s" % (self.mem_usage(), self.cpu_load(), temp, symbol))
        else:
            # default to horizontal
            ui.set('memtemp',
                   " mem cpu temp\n %s%% %s%%  %s%s" % (self.mem_usage(), self.cpu_load(), temp, symbol))
