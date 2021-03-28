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
    import stenogotchi.plugins as plugins
    ObjectClass = plugins.Plugin
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
            print('Plover config file not found')
        
        self.config = config
        
    def get_active_dicts(self):
        if not self.config:
            print('No config file specified')
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
            print(f"Section '{section}' not found in config")
        except configparser.NoOptionError:
            print(f"Option '{option}' not found in section '{section}'")

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
            print ("File '{filepath}' not found")
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
                        help='sort results primarily by number of strokes, secondary by length of strokes. Default, no ordering.')
    parser.add_argument('-v', '--verbose', default=False, action='store_true',
                        help='print additional information')
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
    elif options.verbose:
        pass


if __name__ == '__main__':
    main()


class DictLookup(ObjectClass):
    __autohor__ = 'Anodynous'
    __version__ = '0.1'
    __license__ = 'GPL3'
    __description__ = 'This plugin enables looking up words and strokes in enabled plover dictionaries'

    def __init__(self):
        self._agent = None
        self.running = False
        self.lookup = LookUp()

    def on_loaded(self):
        # delay loading dictionaries to prioritize resources for Plover startup
        logging.debug("[dict_lookup] waiting for Plover to start before fetching dictionaries")
        self.lookup = LookUp()
        
    def on_plover_ready(self):
        logging.debug("[dict_lookup] fetching enabled Plover dictionaries")
        self.running = True
        # Find and read active Plover dictionary contents
        self.lookup.get_config()
        self.lookup.get_active_dicts()
        self.lookup.read_dicts()
        logging.info("[dict_lookup] finished loading entries from all enabled Plover dictionaries")
        if self.options['enable_sorting']:
            self.lookup.set_sort(True)

    def on_ready(self, agent):
        self._agent = agent

    def on_config_changed(self, config):
        self.config = config
                    
    def on_unload(self, ui):
        self.lookup = None

    def lookup_word(self, word):
        self.lookup_word(word)

    def lookup_stroke(self, stroke):
        self.lookup_stroke(stroke)