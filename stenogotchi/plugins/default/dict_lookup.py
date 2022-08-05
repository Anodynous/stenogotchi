#!/usr/bin/env python3

import logging
import time
import random

import stenogotchi.plugins as plugins
from stenogotchi.ui.components import LabeledValue, Text, Line
from stenogotchi.ui.view import BLACK
from stenogotchi.ui import view, state, faces
import stenogotchi.ui.fonts as fonts

class UiHandler():
    def __init__(self, agent):
        self.clear_elements = ('name', 'ups', 'wpm', 'status', 'strokes', 'uptime', 'line1')
        self.input_mode = False
        self._agent = agent
        self._view = view.ROOT
        self._stored_state = state.State()
        self.minion_font = fonts.ImageFont.truetype("%s-Bold" % fonts.FONT_NAME, 18)
        self.minion_offset = 65
     
    def store_state(self):
        for key, element in self._view._state.items():
            if key in self.clear_elements or key == 'face':
                self._stored_state.add_element(key, element)
    
    def restore_state(self):
        # Add all removed items back
        for key, element in self._stored_state.items():
            if key in self.clear_elements:
                self.add_element(key, element)

    def surprise_exit(self):
        if not self._view.get('face') == faces.LOOK_L:
            self._view.set('face', faces.LOOK_L)
            self.update_view()
            time.sleep(1)
        self._view.set('face', faces.LOOK_R)
        self.update_view()
        time.sleep(1)
    
    def relocate_face(self, minion):
        self.remove_element('face')
        if minion:
            # Shrink and relocate
            face = random.choices((faces.LOOK_L_HAPPY, faces.LOOK_L), weights=(0.9, 0.10), k=1)
            self.add_element('face', Text(value=face[0], position=((self._view._width - self.minion_offset + 2), 0), color=BLACK, font=self.minion_font))
        else:
            # Grow and relocate, state doesn't matter as we will update it before view refresh
            self.add_element('face', self._stored_state._state['face'])

    def check_element(self, key):
        return self._view.has_element(key)

    def remove_element(self, key):
        try:
            self._view.remove_element(key)
        except KeyError:
            # TODO: fix self._view.has_element to replace this. Always seems to return None right now.
            logging.error(f"[dict_lookup] No element '{key}' available for removal")

    def add_element(self, key, element):
        self._view.add_element(key, element)

    def update_view(self):
        self._view.update()

    def enable_input_mode(self):
        # Storing current state
        self.store_state()
        # Removing elements we will be overlapping and block them from triggering ui updates   
        for element in self.clear_elements:
            self.remove_element(element)
        # Block update of ui elements we removed
        self._view._ignore_changes = self.clear_elements
        # Shrink stenogotchi face
        self.relocate_face(minion=True)
        # Add new ui elements for input and output        
        line1_offset = self._view._layout['line1'].copy()
        line1_offset[2] = self._view._width - self.minion_offset
        self.add_element('input', LabeledValue(color=BLACK, label='', value='', position=(0, 0) , label_font=fonts.Bold, text_font=fonts.Medium, max_length=29))
        self.add_element('line1_offset', Line(line1_offset, color=BLACK))
        self.add_element('out1', Text(value='', position=self._agent._view._layout['name'], color=BLACK, font=fonts.Bold, wrap=True, max_length=self._agent._view._layout['status']['max']-1))
        self.add_element('out2', Text(value='', position=self._agent._view._layout['status']['pos'], color=BLACK, font=self._agent._view._layout['status']['font'], wrap=True, max_length=self._agent._view._layout['status']['max']))
        self.input_mode = True
        # Used instead of self.update_view() to indicate input position from the start
        self.display_input("")
        logging.debug("[dict_lookup] Enabled dictionary lookup mode")

    def disable_input_mode(self):
        # Add some variety to the exit
        if random.randint(0, 9) > 7:
            self.surprise_exit()
        self._view.remove_element('line1_offset')
        self._view.remove_element('input')
        self._view.remove_element('out1')
        self._view.remove_element('out2')
        # Restore removed elements
        self.restore_state()
        # Grow stenogotchi face
        self.relocate_face(minion=False)
        # revert default update-ignore state
        if self._view._config['ui']['fps'] > 0.0:
            self._view._ignore_changes = ()
        else:
            self._view._ignore_changes = ('uptime', 'name')
        # Prepare new empty state object
        self._stored_state = state.State()
        # Refresh uptime, set return message which will trigger ui update
        self._agent._update_uptime()
        self._agent.set_on_dict_lookup_done()
        
        self.input_mode = False
        logging.debug("[dict_lookup] Disabled dictionary lookup mode")

    def get_input_mode(self):
        return self.input_mode

    def display_output(self, list):
        if self.get_input_mode():
            out1_str = ""
            out2_str = ""
            
            #TODO: handle list items longer than max supported length for column
            cnt = 0
            for item in list:
                if cnt < 6:  # lines 0-5 fit in first column
                    out1_str += f"{item}\n"
                elif cnt < 13:  # lines 6-11 fit in second column
                    out2_str += f"{item}\n"
                else:
                    break  # no more room
                cnt += 1

            self._view.set('out1', out1_str)
            self._view.set('out2', out2_str)
            self.update_view()

    def display_input(self, string, position_indicator="_"):
        if self.get_input_mode():
            string += position_indicator   # Character added to highlight input position
            self._agent._view.set('input', string)
            self.update_view()


class InputHandler():
    # TODO: Add support for evdevkb as input device
    def __init__(self, agent):
        self._agent = agent
        self.input_mode = False
        self._input = ""
    
    def _on_send_string(self, text: str):
        # If enter key received
        if text in ('\n', '\r', '\r\n'):
            if plugins.loaded['dict_lookup'].get_input_mode():
                self._input += " "
                self.push_input(position_indicator="")
                plugins.loaded['dict_lookup'].lookup_word(self._input)
        else:
            self._input += text
            plugins.loaded['dict_lookup'].lookup_word(self._input)
            self.push_input()

    def _on_send_backspaces(self, count: int):
        if count >= len(self._input):
            self.clear_input()
        else:
            self._input = self._input[:-count]
            plugins.loaded['dict_lookup'].lookup_word(self._input)
            self.push_input()

    def _on_send_key_combination(self, combination: str):
        if combination.lower() in ('control(backspace)', 'control_r(backspace)', 'control_l(backspace)'):
            self.clear_input()
        elif combination.lower() == 'escape':
            plugins.loaded['dict_lookup'].disable_input_mode()            
        else:
            logging.warning(f"[dict_lookup] Key-combinations not supported. Input '{combination}' ignored")
    
    def _on_lookup_results(self, results_list):
        # logging.debug(f"[dict_lookup] Lookup result from Plover '{results_list}'")
        plugins.loaded['dict_lookup'].display_lookup_result(results_list)

    def enable_input_mode(self):
        # TODO: trigger routing from evdevkb to here
        command = {'output_to_stenogotchi': True}
        plugins.loaded['plover_link'].send_signal_to_plover(command)
        self.input_mode = True

    def disable_input_mode(self):
        # TODO: revert routing from evdevkb to btclient
        command = {'output_to_stenogotchi': False}
        plugins.loaded['plover_link'].send_signal_to_plover(command)
        self.input_mode = False

    def push_input(self, position_indicator="_"):
        plugins.loaded['dict_lookup'].push_input(self._input, position_indicator)

    def clear_input(self):
        self._input = ""
        self.push_input()


class DictLookup(plugins.Plugin):
    __autohor__ = 'Anodynous'
    __version__ = '0.4'
    __license__ = 'GPL3'
    __description__ = 'This plugin enables looking up words and strokes in enabled plover dictionaries'

    def __init__(self):
        self._agent = None
        self.config = None
        self.running = False
        self.input_mode = False
        self.input_handler = None 
        self.ui_handler = None

    def on_plover_ready(self, agent):
        self._agent = agent
        self.ui_handler = UiHandler(agent)
        self.input_handler = InputHandler(agent)
        self.running = True

    def on_config_changed(self, config):
        self.config = config
                    
    def on_unload(self, ui):
        self.lookup = None
        self.ui_handler = None

    def get_running(self):
        return self.running

    def get_input_mode(self):
        return self.input_mode

    def enable_input_mode(self):
        self.ui_handler.enable_input_mode()
        self.input_handler.enable_input_mode()
        self.input_mode = True

    def disable_input_mode(self):
        self.ui_handler.disable_input_mode()
        self.input_handler.disable_input_mode()
        self.input_handler.clear_input()
        self.input_mode = False

    def lookup_word(self, word):
        # Remove leading/trailing whitespaces and send word to plover for dictionary lookup
        word = word.strip()
        command = {'lookup_word': word}
        plugins.loaded['plover_link'].send_signal_to_plover(command)

    def lookup_stroke(self, stroke):
        # Remove leading/trailing whitespaces and send stroke to plover for dictionary lookup
        # TODO: implement functionality to use stroke-lookup
        stroke = stroke.strip()
        logging.debug(f"[dict_lookup] Looking up stroke '{stroke}'")
        command = {'lookup_word': stroke}
        plugins.loaded['plover_link'].send_signal_to_plover(command)
   
    def display_lookup_result(self, results_list):
        self.push_output(results_list)

    def sort_list(self, rlist):
        # Sorts the results in ascending order.
        # Primary sorting key: number of chords
        # Secondary sorting key: length of chord(combination)
        sort_key = lambda k : (k.count('/'), len(k))
        rlist_sorted = []
        if len(rlist) < 2:
            return rlist
        else:
            rlist_sorted = sorted(rlist, key=sort_key)
            return rlist_sorted

    def push_input(self, string="", position_indicator="_"):
        if self.input_mode:
            self.ui_handler.display_input(string, position_indicator)
    
    def push_output(self, rlist):
        if self.input_mode:
            if rlist:
                rlist_sorted = self.sort_list(rlist)
            else:
                rlist_sorted = []
            self.ui_handler.display_output(rlist_sorted)        
        
if __name__ == '__main__':
    print("Please enable and run as Stenogotchi plugin")