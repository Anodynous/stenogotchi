import _thread
from threading import Lock
import time
import logging
import random
from PIL import ImageDraw

import stenogotchi
import stenogotchi.utils as utils
import stenogotchi.plugins as plugins
from stenogotchi.voice import Voice

import stenogotchi.ui.web as web
import stenogotchi.ui.fonts as fonts
import stenogotchi.ui.faces as faces
from stenogotchi.ui.components import *
from stenogotchi.ui.state import State

WHITE = 0xff
BLACK = 0x00
ROOT = None


class View(object):
    def __init__(self, config, impl, state=None):
        global ROOT

        # setup faces from the configuration in case the user customized them
        faces.load_from_config(config['ui']['faces'])

        self._agent = None
        self._render_cbs = []
        self._config = config
        self._canvas = None
        self._frozen = False
        self._lock = Lock()
        self._voice = Voice(lang=config['main']['lang'])
        self._implementation = impl
        self._layout = impl.layout()
        self._width = self._layout['width']
        self._height = self._layout['height']
        self._state = State(state={
            'ups': LabeledValue(color=BLACK, label='BAT', value='000', position=self._layout['ups'],
                                    label_font=fonts.Bold,
                                    text_font=fonts.Medium),
            'aps': LabeledValue(color=BLACK, label='APS', value='0 (00)', position=self._layout['aps'],
                                label_font=fonts.Bold,
                                text_font=fonts.Medium),

            'uptime': LabeledValue(color=BLACK, label='UP', value='00:00:00', position=self._layout['uptime'],
                                   label_font=fonts.Bold,
                                   text_font=fonts.Medium),

            'line1': Line(self._layout['line1'], color=BLACK),
            'line2': Line(self._layout['line2'], color=BLACK),

            'face': Text(value=faces.SLEEP, position=self._layout['face'], color=BLACK, font=fonts.Huge),

            'friend_face': Text(value=None, position=self._layout['friend_face'], font=fonts.Bold, color=BLACK),
            'friend_name': Text(value=None, position=self._layout['friend_name'], font=fonts.BoldSmall,
                                color=BLACK),

            'name': Text(value='%s>' % 'stenogotchi', position=self._layout['name'], color=BLACK, font=fonts.Bold),

            'status': Text(value=self._voice.default(),
                           position=self._layout['status']['pos'],
                           color=BLACK,
                           font=self._layout['status']['font'],
                           wrap=True,
                           # the current maximum number of characters per line, assuming each character is 6 pixels wide
                           max_length=self._layout['status']['max']),

            'bthost': LabeledValue(label='BT', value='', color=BLACK,
                                   position=self._layout['bthost']['pos'], label_font=fonts.Bold,
                                   text_font=fonts.Medium, max_length=self._layout['bthost']['max']),
            'wifi': LabeledValue(label='WIFI', value='', color=BLACK,
                                   position=self._layout['wifi']['pos'], label_font=fonts.Bold,
                                   text_font=fonts.Medium, max_length=self._layout['wifi']['max']),
            'mode': Text(value='NONE', position=self._layout['mode'],
                         font=fonts.Bold, color=BLACK),
        })

        if state:
            for key, value in state.items():
                self._state.set(key, value)

        plugins.on('ui_setup', self)

        if config['ui']['fps'] > 0.0:
            _thread.start_new_thread(self._refresh_handler, ())
            self._ignore_changes = ()
        else:
            logging.warning("ui.fps is 0, the display will only update for major changes")
            self._ignore_changes = ('uptime', 'name')

        ROOT = self

    def set_agent(self, agent):
        self._agent = agent

    def has_element(self, key):
        self._state.has_element(key)

    def add_element(self, key, elem):
        self._state.add_element(key, elem)

    def remove_element(self, key):
        self._state.remove_element(key)

    def width(self):
        return self._width

    def height(self):
        return self._height

    def on_state_change(self, key, cb):
        self._state.add_listener(key, cb)

    def on_render(self, cb):
        if cb not in self._render_cbs:
            self._render_cbs.append(cb)

    def _refresh_handler(self):
        delay = 1.0 / self._config['ui']['fps']
        while True:
            try:
                name = self._state.get('name')
                self.set('name', name.rstrip('█').strip() if '█' in name else (name + ' █'))
                self.update()
            except Exception as e:
                logging.warning("non fatal error while updating view: %s" % e)

            time.sleep(delay)

    def set(self, key, value):
        self._state.set(key, value)

    def get(self, key):
        return self._state.get(key)

    def on_starting(self):
        self.set('status', self._voice.on_starting() + ("\n(v%s)" % stenogotchi.__version__))
        self.set('face', faces.AWAKE)
        self.update()

    def on_manual_mode(self, last_session):
        self.set('mode', 'MANU')
        self.set('face', faces.HAPPY)
        self.set('status', self._voice.on_last_session_data(last_session))
        self.set('uptime', last_session.duration)
        self.update()

    def is_normal(self):
        return self._state.get('face') not in (
            faces.INTENSE,
            faces.COOL,
            faces.BORED,
            faces.HAPPY,
            faces.EXCITED,
            faces.MOTIVATED,
            faces.DEMOTIVATED,
            faces.SMART,
            faces.SAD,
            faces.LONELY)

    def on_keys_generation(self):
        self.set('face', faces.AWAKE)
        self.set('status', self._voice.on_keys_generation())
        self.update()

    def on_normal(self):
        self.set('face', faces.AWAKE)
        self.set('status', self._voice.on_normal())
        self.update()

    def on_reading_logs(self, lines_so_far=0):
        self.set('face', faces.SMART)
        self.set('status', self._voice.on_reading_logs(lines_so_far))
        self.update()

    def wait(self, secs, sleeping=True):
        was_normal = self.is_normal()
        part = secs / 10.0

        for step in range(0, 10):
            # if we weren't in a normal state before going
            # to sleep, keep that face and status on for
            # a while, otherwise the sleep animation will
            # always override any minor state change before it
            if was_normal or step > 5:
                if sleeping:
                    if secs > 1:
                        self.set('face', faces.SLEEP)
                        self.set('status', self._voice.on_napping(int(secs)))
                    else:
                        self.set('face', faces.SLEEP2)
                        self.set('status', self._voice.on_awakening())
                else:
                    self.set('status', self._voice.on_waiting(int(secs)))
                    good_mood = self._agent.in_good_mood()
                    if step % 2 == 0:
                        self.set('face', faces.LOOK_R_HAPPY if good_mood else faces.LOOK_R)
                    else:
                        self.set('face', faces.LOOK_L_HAPPY if good_mood else faces.LOOK_L)

            time.sleep(part)
            secs -= part

        self.on_normal()

    def on_shutdown(self):
        self.set('face', faces.SLEEP)
        self.set('status', self._voice.on_shutdown())
        self.update(force=True)
        self._frozen = True

    def on_bored(self):
        self.set('face', faces.BORED)
        self.set('status', self._voice.on_bored())
        self.update()

    def on_sad(self):
        self.set('face', faces.SAD)
        self.set('status', self._voice.on_sad())
        self.update()

    def on_angry(self):
        self.set('face', faces.ANGRY)
        self.set('status', self._voice.on_angry())
        self.update()

    def on_motivated(self, reward):
        self.set('face', faces.MOTIVATED)
        self.set('status', self._voice.on_motivated(reward))
        self.update()

    def on_demotivated(self, reward):
        self.set('face', faces.DEMOTIVATED)
        self.set('status', self._voice.on_demotivated(reward))
        self.update()

    def on_excited(self):
        self.set('face', faces.EXCITED)
        self.set('status', self._voice.on_excited())
        self.update()

    def on_miss(self, who):
        self.set('face', faces.SAD)
        self.set('status', self._voice.on_miss(who))
        self.update()

    def on_grateful(self):
        self.set('face', faces.GRATEFUL)
        self.set('status', self._voice.on_grateful())
        self.update()

    def on_lonely(self):
        self.set('face', faces.LONELY)
        self.set('status', self._voice.on_lonely())
        self.update()

    def on_rebooting(self):
        self.set('face', faces.BROKEN)
        self.set('status', self._voice.on_rebooting())
        self.update()

    def on_custom(self, text):
        self.set('face', faces.DEBUG)
        self.set('status', self._voice.custom(text))
        self.update()
    
    def on_plover_boot(self):
        self.set('face', faces.SLEEP)
        self.set('status', self._voice.on_plover_boot())
        self.update()

    def on_plover_ready(self):
        self.set('face', faces.AWAKE)
        self.set('status', self._voice.on_plover_ready())
        self.update()

    def on_bt_connected(self, bthost_name):
        self.set('face', faces.LOOK_L_HAPPY)
        self.set('status', f'Latched bluetooth tentacle to {bthost_name}')
        self.update()

    def on_bt_disconnected(self):
        self.set('face', faces.INTENSE)
        self.set('status', 'Lost bluetooth connection')
        self.update()

    def on_wifi_connected(self, ssid, ip):
        self.set('face', faces.COOL)
        self.set('status', f'Found a town called {ssid}. I\'m gonna be known as {ip}')
        self.update()

    def on_wifi_disconnected(self):
        self.set('face', faces.LONELY)
        self.set('status', self._voice.on_wifi_disconnected())
        self.update()

    def update(self, force=False, new_data={}):
        for key, val in new_data.items():
            self.set(key, val)

        with self._lock:
            if self._frozen:
                return

            state = self._state
            changes = state.changes(ignore=self._ignore_changes)
            if force or len(changes):
                self._canvas = Image.new('1', (self._width, self._height), WHITE)
                drawer = ImageDraw.Draw(self._canvas)

                plugins.on('ui_update', self)

                for key, lv in state.items():
                    lv.draw(self._canvas, drawer)

                web.update_frame(self._canvas)

                for cb in self._render_cbs:
                    cb(self._canvas)

                self._state.reset()
