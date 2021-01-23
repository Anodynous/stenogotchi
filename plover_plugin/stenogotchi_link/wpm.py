#!/usr/bin/env python3
#
# Based on: https://github.com/arxanas/plover_wpm_meter.git, modified to remove QT dependency.
# 
# This is a plugin for Plover to display your typing speed as you type, in either or both of words per minute or strokes per minute:
##  Words per minute: Shows the rate at which you stroked words in the last 10 and 60 seconds.
##  Strokes per minute: Shows how efficiently you stroked words in the last 10 and 60 seconds. Lower values are more efficient, e.g. a value of 1 means that on average it took you one stroke to write out a word.
#
# A word is defined in one of three ways:
##    NCRA: The National Court Reporters Association defines a “word” as 1.4 syllables. This is the measure used for official NCRA testing material.
##    Traditional: The traditional metric for “word” in the context of keyboarding is defined to be 5 characters per word, including spaces. This is compatible with the notion of “word” in many typing speed utilities.
##    Spaces: A word is a whitespace-separated sequence of characters. This metric of course doesn’t take into account the fact that some words are longer than others, both in length and syllables.

import time
from threading import Timer
from textstat.textstat import textstat

from plover.formatting import OutputHelper

class RepeatTimer(Timer):
    """ 
    Perpetually repeating timer implementation of threading.Timer
    """  

    def run(self):
        while not self.finished.wait(self.interval):
            self.function(*self.args, **self.kwargs)

class CaptureOutput(object):
   
    def __init__(self, chars):
        self.chars = chars

    def send_backspaces(self, n):
        del self.chars[-n:]

    def send_string(self, s):
        self.chars += _timestamp_items(s)

    def send_key_combination(self, c):
        pass

    def send_engine_command(self, c):
        pass


class BaseMeter():
  
    def __init__(self):
        # Set timer to calculate wpm/strokes stats each second
        self._timer = RepeatTimer(1, self.on_timer)
        self._timer.start()
        # Set timer to publish wpm/strokes stats each minute
        self._event_timer = RepeatTimer(60, self.trigger_event_update)
        self._event_timer.start()
        self.chars = []

    def on_translation(self, old, new):
        output = CaptureOutput(self.chars)
        output_helper = OutputHelper(output, False, False)
        output_helper.render(None, old, new)

    def on_timer(self):
        raise NotImplementedError()

    def trigger_event_update(self):
        raise NotImplementedError()


class PloverWpmMeter(BaseMeter):

    _TIMEOUTS = {
        "wpm10": 10,
        "wpm60": 60,
    }

    def __init__(self, stenogotchi_link, wpm_method='ncra'):
        super().__init__()
        self._stenogotchi_link = stenogotchi_link
        self.strokes = []
        self.wpm_methods = {
            'ncra': False,          # NCRA (by syllables)
            'traditional': False,   # Traditional (by characters)
            'spaces': False,        # Spaces (by whitespace)
        }
        self.set_wpm_method(wpm_method)
        self.wpm_stats = {}

    def set_wpm_method(self, method):
        self.wpm_methods = dict.fromkeys(self.wpm_methods, False)
        self.wpm_methods[method] = True

    def get_wpm_method(self):
        for method, enabled in self.wpm_methods.items():
            if enabled:
                return method

    def get_stats(self):
        return self.wpm_stats

    def on_timer(self):
        max_timeout = max(self._TIMEOUTS.values())
        self.chars = _filter_old_items(self.chars, max_timeout)
        for name, timeout in self._TIMEOUTS.items():
            chars = _filter_old_items(self.chars, timeout)
            wpm = _wpm_of_chars(chars, method=self.get_wpm_method())
            self.wpm_stats[name] = str(wpm)

    def trigger_event_update(self):
        self._stenogotchi_link._on_wpm_meter_update_wpm(stats=self.wpm_stats)
        

class PloverStrokesMeter(BaseMeter):

    _TIMEOUTS = {
        "strokes10": 10,
        "strokes60": 60,
    }

    def __init__(self, stenogotchi_link, strokes_method='ncra'):
        super().__init__()
        self._stenogotchi_link = stenogotchi_link
        self.actions = []
        self.strokes_methods = {
            'ncra': False,          # NCRA (by syllables)
            'traditional': False,   # Traditional (by characters)
            'spaces': False,        # Spaces (by whitespace)
        }
        self.set_strokes_method(strokes_method)
        self.strokes_stats = {}
       
        # By default, the QLCDNumbers will just display "0", without a decimal
        # point, on initial render. Render them ourselves so that we don't
        # switch from "0" to "0.00" after a second.
        self.on_timer()

    def set_strokes_method(self, method):
        self.strokes_methods = dict.fromkeys(self.strokes_methods, False)
        self.strokes_methods[method] = True

    def get_strokes_method(self):
        for method, enabled in self.strokes_methods.items():
            if enabled:
                return method

    def get_stats(self):
        return self.strokes_stats

    def on_translation(self, old, new):
        super().on_translation(old, new)
        if len(old) > 0:
            self.actions = self.actions[:-len(old)]
        self.actions += _timestamp_items(new)

    def on_timer(self):
        max_timeout = max(self._TIMEOUTS.values())
        self.chars = _filter_old_items(self.chars, max_timeout)
        self.actions = _filter_old_items(self.actions, max_timeout)
        for name, timeout in self._TIMEOUTS.items():
            chars = _filter_old_items(self.chars, timeout)
            num_strokes = len(_filter_old_items(self.actions, timeout))
            strokes_per_word = _spw_of_chars(
                num_strokes,
                chars,
                method=self.get_strokes_method()
            )
            self.strokes_stats[name] = str("{:0.2f}".format(strokes_per_word))

    def trigger_event_update(self):
        self._stenogotchi_link._on_wpm_meter_update_strokes(stats=self.strokes_stats)

def _timestamp_items(items):
    current_time = time.time()
    return [(i, current_time) for i in items]


def _filter_old_items(items, timeout):
    current_time = time.time()
    return [(i, t) for i, t in items
            if (current_time - t) <= timeout]


def _words_in_chars(chars, method):
    text = "".join(c for c, _ in chars)
    if method == "ncra":
        # The NCRA defines a "word" to be 1.4 syllables, which is the average
        # number of syllables per English word.
        syllables_per_word = 1.4
        # For some reason, textstat returns syllable counts such as a
        # one-syllable word like "the" being 0.9 syllables.
        syllables_in_text = textstat.syllable_count(text) / 0.9
        return syllables_in_text * (1 / syllables_per_word)
    elif method == "traditional":
        # Formal definition; see https://en.wikipedia.org/wiki/Words_per_minute
        return len(text) / 5
    elif method == "spaces":
        return len([i for i in text.split() if i])
    else:
        assert False, "bad wpm method: " + method


def _time_interval_of_chars(chars):
    start_time = min(t for _, t in chars)
    current_time = time.time()
    time_interval = current_time - start_time
    time_interval = max(1, time_interval)
    return time_interval


def _wpm_of_chars(chars, method):
    num_words = _words_in_chars(chars, method)
    if not num_words:
        return 0

    time_interval = _time_interval_of_chars(chars)
    num_minutes = time_interval / 60
    num_words_per_minute = num_words / num_minutes
    return int(round(num_words_per_minute))


def _spw_of_chars(num_strokes, chars, method):
    num_words = _words_in_chars(chars, method)
    if not num_words:
        return 0

    return num_strokes / num_words


def _spw_of_chars(num_strokes, chars, method):
    num_words = _words_in_chars(chars, method)
    if not num_words:
        return 0

    return num_strokes / num_words