import time
import json
import os
import re
import logging
import asyncio
import _thread

import stenogotchi
import stenogotchi.utils as utils
import stenogotchi.plugins as plugins
from stenogotchi.ui.web.server import Server
from stenogotchi.automata import Automata
#from stenogotchi.log import LastSession

RECOVERY_DATA_FILE = '/root/.stenogotchi-recovery'


class Agent(Automata):
    def __init__(self, view, config):
        Automata.__init__(self, config, view)
        self._started_at = time.time()
        self._view = view
        self._view.set_agent(self)
        self._web_ui = None
        self._wifi_connected = None

        self._history = {}
        #self.last_session = LastSession(self._config)
        self.mode = 'auto'

        logging.info("%s (v%s)", stenogotchi.name(), stenogotchi.__version__)
        for _, plugin in plugins.loaded.items():
            logging.debug("plugin '%s' v%s", plugin.__class__.__name__, plugin.__version__)

    def config(self):
        return self._config

    def view(self):
        return self._view

    def start(self):
        self.set_starting()
        # self.start_event_polling()
        # print initial stats
        self.start_session_fetcher()
        self.set_ready()

    def _update_uptime(self):
        secs = stenogotchi.uptime()
        self._view.set('uptime', utils.secs_to_hhmmss(secs))

    def _update_wifi(self):
        status, ip = stenogotchi.get_wifi_status()
  
        if status == 'UP':
            if self._wifi_connected:
                return
            ssid = stenogotchi.get_wifi_ssid()
            if ssid and ip:
                self._wifi_connected = True
                # Create web-ui only once a wifi connection is established
                if not self._web_ui:
                    self._web_ui = Server(self, self._config['ui'])
            else:
                if not ssid:
                    ssid = "[Searching]"
                    ip = "the ghost"
                if not ip:
                    ip = "the ghost"
                self._wifi_connected = False
            self.set_wifi_connected(ssid, ip)
        elif status == 'DOWN' or not status:
            if self._wifi_connected == False:
                return
            self._wifi_connected = False
            self.set_wifi_disconnected('[OFF]')

    def _reboot(self):
        self.set_rebooting()
        self._save_recovery_data()
        stenogotchi.reboot()

    def _save_recovery_data(self):
        logging.warning("writing recovery data to %s ...", RECOVERY_DATA_FILE)
        with open(RECOVERY_DATA_FILE, 'w') as fp:
            data = {
                'started_at': self._started_at,
                'history': self._history,
            }
            json.dump(data, fp)

    def _load_recovery_data(self, delete=True, no_exceptions=True):
        try:
            with open(RECOVERY_DATA_FILE, 'rt') as fp:
                data = json.load(fp)
                logging.info("found recovery data: %s", data)
                self._started_at = data['started_at']
                self._history = data['history']

                if delete:
                    logging.info("deleting %s", RECOVERY_DATA_FILE)
                    os.unlink(RECOVERY_DATA_FILE)
        except:
            if not no_exceptions:
                raise


    def start_session_fetcher(self):
        _thread.start_new_thread(self._fetch_stats, ())

    async def plover_status_update(self, msg):
        pass

    def _fetch_stats(self):
        while True:
            #s = self.session()    # this is just the request object for connection to bettercap -> to be used for fetching plover stats instead
            self._update_uptime()
            self._update_wifi()
            time.sleep(30)

    async def _on_event(self, msg):    # no bettercap to produce events for us, to be used for plover events
        pass

    def _event_poller(self, loop):
        self._load_recovery_data()
        #while True:


    def start_event_polling(self):
        # start a thread and pass in the mainloop
        _thread.start_new_thread(self._event_poller, (asyncio.get_event_loop(),))
