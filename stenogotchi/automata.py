import logging

import stenogotchi.plugins as plugins


# basic mood system
class Automata(object):
    def __init__(self, config, view):
        self._config = config
        self._view = view

    def set_starting(self):
        self._view.on_starting()

    def set_ready(self):
        plugins.on('ready', self)

    def in_good_mood(self):
        pass

    # triggered when it's a sad/bad day but you have good friends around ^_^
    def set_grateful(self):
        self._view.on_grateful()
        plugins.on('grateful', self)

    def set_lonely(self):
        self._view.on_lonely()
        plugins.on('lonely', self)

    def set_bored(self):
        self._view.on_bored()
        plugins.on('bored', self)

    def set_sad(self):
        self._view.on_sad()
        plugins.on('sad', self)

    def set_angry(self):
        self._view.on_angry()
        plugins.on('angry', self)

    def set_excited(self):
        self._view.on_excited()
        plugins.on('excited', self)

    def set_rebooting(self):
        self._view.on_rebooting()
        plugins.on('rebooting', self)

    def wait_for(self, t, sleeping=True):
        self._view.wait(t, sleeping)

    def set_plover_boot(self):
        self._view.on_plover_boot()
        plugins.on('plover_boot', self)

    def set_plover_ready(self):
        self._view.on_plover_ready()
        plugins.on('plover_ready', self)

    def set_plover_quit(self):
        self._view.on_plover_quit()
        plugins.on('plover_quit', self)
        
    def set_bt_connected(self, bthost_name):
        self._view.set('bthost', bthost_name)
        self._view.on_bt_connected(bthost_name)
        plugins.on('bt_connected', self, bthost_name)

    def set_bt_disconnected(self):
        self._view.set('bthost', "")
        self._view.on_bt_disconnected()
        plugins.on('bt_disconnected', self)
        
    def set_wifi_connected(self, ssid, ip):
        self._view.set('wifi', ssid)
        self._view.on_wifi_connected(ssid, ip)
        plugins.on('wifi_connected', self, ssid, ip)

    def set_wifi_disconnected(self, ssid=''):
        self._view.set('wifi', ssid)
        self._view.on_wifi_disconnected()
        plugins.on('wifi_disconnected', self)

    def set_wpm_stats(self, stats):
        self._view.on_set_wpm(stats)
        plugins.on('wpm_set', self)

    def set_strokes_stats(self, stats):
        self._view.on_set_strokes(stats)
        plugins.on('strokes_set', self)

