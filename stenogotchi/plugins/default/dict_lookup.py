#!/usr/bin/env python3

import os
import logging
import argparse
import appdirs
import configparser
import json
import re
import time

from collections import OrderedDict
from collections.abc import Mapping, MutableMapping

if not __name__ == '__main__':
    import random
    import stenogotchi.plugins as plugins
    ObjectClass = plugins.Plugin
    from stenogotchi.ui.components import LabeledValue, Text, Line
    from stenogotchi.ui.view import BLACK
    from stenogotchi.ui import view, state, faces
    import stenogotchi.ui.fonts as fonts
else:
    ObjectClass = object

class CaseInsensitiveDict(MutableMapping):
    """ Taken from Requests: https://github.com/psf/requests/blob/master/requests/structures.py#L15
    A case-insensitive ``dict``-like object.
    Implements all methods and operations of
    ``MutableMapping`` as well as dict's ``copy``. Also
    provides ``lower_items``.
    All keys are expected to be strings. The structure remembers the
    case of the last key to be set, and ``iter(instance)``,
    ``keys()``, ``items()``, ``iterkeys()``, and ``iteritems()``
    will contain case-sensitive keys. However, querying and contains
    testing is case insensitive::
        cid = CaseInsensitiveDict()
        cid['Accept'] = 'application/json'
        cid['aCCEPT'] == 'application/json'  # True
        list(cid) == ['Accept']  # True
    For example, ``headers['content-encoding']`` will return the
    value of a ``'Content-Encoding'`` response header, regardless
    of how the header name was originally stored.
    If the constructor, ``.update``, or equality comparison
    operations are given keys that have equal ``.lower()``s, the
    behavior is undefined.
    """

    def __init__(self, data=None, **kwargs):
        self._store = OrderedDict()
        if data is None:
            data = {}
        self.update(data, **kwargs)

    def __setitem__(self, key, value):
        # Use the lowercased key for lookups, but store the actual
        # key alongside the value.
        self._store[key.lower()] = (key, value)

    def __getitem__(self, key):
        return self._store[key.lower()][1]

    def __delitem__(self, key):
        del self._store[key.lower()]

    def __iter__(self):
        return (casedkey for casedkey, mappedvalue in self._store.values())

    def __len__(self):
        return len(self._store)

    def lower_items(self):
        """Like iteritems(), but with all lowercase keys."""
        return (
            (lowerkey, keyval[1])
            for (lowerkey, keyval)
            in self._store.items()
        )

    def __eq__(self, other):
        if isinstance(other, Mapping):
            other = CaseInsensitiveDict(other)
        else:
            return NotImplemented
        # Compare insensitively
        return dict(self.lower_items()) == dict(other.lower_items())

    # Copy is required
    def copy(self):
        return CaseInsensitiveDict(self._store.values())

    def __repr__(self):
        return str(dict(self.items()))

class LookUp():
    def __init__(self):
        self.config_dir = None
        self.config = None
        self.enable_sorting = False
        self.active_dict_paths = [] 
        self.dict_names = []
        self.dict_lists_strokes = []
        self.dict_lists_words = []

    def get_config(self):
        self.config_dir = appdirs.user_data_dir('plover', 'plover')
        config_file = os.path.join(self.config_dir, "plover.cfg")
        config = configparser.ConfigParser()
        config.read(config_file)

        if len(config.sections()) == 0:
            config = None
            logging.warning('[dict_lookup] Plover config file not found')
        
        self.config = config
        
    def get_active_dicts(self):
        if not self.config:
            logging.warning('[dict_lookup] No Plover config file specified')
            return

        section = None
        option = 'dictionaries'
        try:
            # Get section with dictionaries and convert to json object
            for section in self.config.sections():
                if self.config.has_option(section, option):
                    all_dicts = json.loads(self.config.get(section, option))
                    # Get paths of of enabled dictionaries. Prepend config_dir to path where needed.
                    for x in all_dicts:
                        if x['enabled']:
                            self.active_dict_paths.append(self.get_full_path(x['path']))

        except configparser.NoSectionError:
            logging.exception(f"[dict_lookup] Section '{section}' not found in config")
        except configparser.NoOptionError:
            logging.exception(f"[dict_lookup] Option '{option}' not found in section '{section}'")

    def get_full_path(self, filepath):
        """ Appends Plover config_dir to path where needed and returns full os path for accessing file.
            Returns None if file cannot be located
        """
        joined_path = os.path.join(self.config_dir, filepath)
        
        if os.path.isfile(filepath):
            return filepath
        elif os.path.isfile(joined_path):
            return joined_path
        else:
            logging.warning(f"[dict_lookup] File '{filepath}' not found")
            return None

    def read_dicts(self):
        """ Reads all active Plover dictionaries into separate lists of dictionaries 
        dict_lists_strokes = 'stroke' : 'word'
        dict_lists_words = 'word' : 'strokes'
        """
        for path in self.active_dict_paths:
            self.dict_names.append(os.path.basename(path))
            with open(path,'r',encoding='UTF-8') as src:
                dict_map = json.load(src)
                self.dict_lists_strokes.append(dict_map)
            # Inverted version using Requests implementation of CaseInsensitiveDict for word lookups
                inv_map = CaseInsensitiveDict()
                for k, v in dict_map.items():
                    inv_map[v] = inv_map.get(v, []) + [k]
                self.dict_lists_words.append(inv_map)
   
    def set_sort(self, boolean):
        self.enable_sorting = boolean

    def sort(self, rlist):
        if self.enable_sorting:
            sort_key = lambda k : (k.count('/'), len(k))
        else:
            return rlist

        sorted_rlist = []
        if len(rlist) < 2:
            return rlist
        else:
            sorted_rlist = sorted(rlist, key=sort_key)
            return sorted_rlist

    def lookup(self, key, type='word'):
        i = 0
        full_results = {}
        dict_lists = []
        if type == 'word':
            # No need for case normalization due to using CaseInsensitiveDict
            dict_lists = self.dict_lists_words
        elif type == 'stroke':
            dict_lists = self.dict_lists_strokes
            # All strokes are in uppercase, ensure our key matchese this
            key = key.upper()
        
        for dict in dict_lists:
            result = dict.get(key)
            if result:
                # Sort output based on method given (default is None).
                if type == 'word':
                    full_results[self.dict_names[i]] = self.sort(result)
                else:  # No sorting needed for stroke lookup
                    full_results[self.dict_names[i]] = result

            i += 1
        return full_results

def main():
    parser = argparse.ArgumentParser(description='Lookup words or strokes in active Plover dictionaries')
    parser.add_argument('-w', '--word', default=False, action='store_true',
                        help='lookup stroke for given word')
    parser.add_argument('-s', '--stroke', default=False, action='store_true',
                        help='lookup translation of stroke')
    parser.add_argument('-o', '--order', default=False, action='store_true',
                        help='sort results primarily by number of strokes, secondary by length of strokes. Default is no ordering.')
    parser.add_argument('words', nargs='+', help='word(s) to look up')

    options = parser.parse_args()
    words = options.words
    words = " ".join(words)

    lookup = LookUp()
    # Find and read active Plover dictionary contents
    lookup.get_config()
    lookup.get_active_dicts()
    lookup.read_dicts()

    if options.order:
        lookup.set_sort(True)

    if options.word:
        print(lookup.lookup(words, type='word'))
    elif options.stroke:
        print(lookup.lookup(words, type='stroke'))

if __name__ == '__main__':
    main()

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

    def relocate_face(self, minion):
        self.remove_element('face')
        if minion:
            # Shrink and relocate
            face = random.choices((faces.LOOK_L_HAPPY, faces.LOOK_L), weights=(0.8, 0.2), k=1)
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
            logging.debug(f"[dict_lookup] No element '{key}' available for removal")

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
        self.add_element('input', LabeledValue(color=BLACK, label='>', value='', position=(0, 0) , label_font=fonts.Bold, text_font=fonts.Medium, max_length=29))
        self.add_element('line1_offset', Line(line1_offset, color=BLACK))
        self.add_element('out1', Text(value='', position=self._agent._view._layout['name'], color=BLACK, font=fonts.Bold, wrap=True, max_length=self._agent._view._layout['status']['max']-1))
        self.add_element('out2', Text(value='', position=self._agent._view._layout['status']['pos'], color=BLACK, font=self._agent._view._layout['status']['font'], wrap=True, max_length=self._agent._view._layout['status']['max']))
        self.update_view()
        self.input_mode = True
        logging.info("[dict_lookup] Enabled dictionary lookup mode")

    def disable_input_mode(self):
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
        logging.info("[dict_lookup] Disabled dictionary lookup mode")

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
                    out1_str += f"{item} \n"
                elif cnt < 13:  # lines 6-11 fit in second column
                    out2_str += f"{item} \n"
                else:
                    break  # no more room
                cnt += 1

            self._view.set('out1', out1_str)
            self._view.set('out2', out2_str)
            self.update_view()

    def display_input(self, string):
        if self.get_input_mode():
            self._agent._view.set('input', string)
            self.update_view()


class InputHandler():
    # TODO: Add support for evdevkb as input device
    def __init__(self, agent):
        self._agent = agent
        self.input_mode = False
        self._input = ""
    
    def _on_send_string(self, text: str):
        self._input += text
        self.push_input()

    def _on_send_backspaces(self, count: int):
        if count > len(self._input):
            self.clear_input()
        else:
            self._input = self._input[:-count]
        self.push_input()

    def _on_send_key_combination(self, combination: str):
        if combination == 'Return':
            if plugins.loaded['dict_lookup'].get_input_mode():
                result_dict = plugins.loaded['dict_lookup'].lookup_word(self._input)
                plugins.loaded['dict_lookup'].display_lookup_result(result_dict)
        else:
            logging.warning(f"[dict_lookup] Received unhandled input combination: '{combination}'")
    
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

    def push_input(self):
        plugins.loaded['dict_lookup'].push_input(self._input)

    def clear_input(self):
        self._input = ""


class DictLookup(ObjectClass):
    __autohor__ = 'Anodynous'
    __version__ = '0.2'
    __license__ = 'GPL3'
    __description__ = 'This plugin enables looking up words and strokes in enabled plover dictionaries'

    def __init__(self):
        self._agent = None
        self.config = None
        self.running = False
        self.input_mode = False
        self.lookup = LookUp()
        self.input_handler = None 
        self.ui_handler = None

    def on_loaded(self):
        # delay loading dictionaries to prioritize resources for Plover startup
        logging.debug("[dict_lookup] Waiting for Plover to start before fetching dictionaries")
        self.lookup = LookUp()

    def on_plover_ready(self, agent):
        self._agent = agent
        self.ui_handler = UiHandler(agent)
        self.input_handler = InputHandler(agent)

        logging.debug("[dict_lookup] Fetching enabled Plover dictionaries")
        # Find and read active Plover dictionary contents
        self.lookup.get_config()
        self.lookup.get_active_dicts()
        self.lookup.read_dicts()
        self.running = True
        logging.info("[dict_lookup] Finished loading entries from all enabled Plover dictionaries")
        if self.options['enable_sorting']:
            self.lookup.set_sort(True)

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
        # Remove leading/trailing whitespaces
        word = word.strip()
        logging.debug(f"[dict_lookup] Looking up word '{word}'")
        dict_result = self.lookup.lookup(word, type='word')
        return dict_result

    def lookup_stroke(self, stroke):
        # Remove leading/trailing whitespaces
        stroke = stroke.strip()
        logging.debug(f"[dict_lookup] Looking up stroke '{stroke}'")
        dict_result = self.lookup.lookup(stroke, type='stroke')
        return dict_result
    
    def display_lookup_result(self, dict):
        result_list = []
        for key in dict:
            for item in dict[key]:
                result_list.append(item)
        
        self.push_output(result_list)

    def push_input(self, string):
        if self.input_mode:
            self.ui_handler.display_input(string)
    
    def push_output(self, flat_list):
        if self.input_mode:
            self.ui_handler.display_output(flat_list)        
        