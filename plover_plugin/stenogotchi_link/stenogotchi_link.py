#!/usr/bin/env python3
# This is a Plover plugin acting as link between Plover and Stenogotchi
# Based on: https://github.com/nsmarkop/plover_websocket_server

import plover.log
import json
import jsonpickle
from typing import Optional, List
from time import sleep

from plover.engine import StenoEngine
from plover.steno import Stroke
from plover.config import Config
from plover.formatting import _Action
from plover.steno_dictionary import StenoDictionaryCollection

from stenogotchi_link.clients import BTClient, StenogotchiClient
from stenogotchi_link.wpm import PloverWpmMeter, PloverStrokesMeter


ERROR_MISSING_ENGINE = 'Plover engine not provided'


class EngineServer():
    """
    Hooks into Plover events and makes them available to Stenogotchi.
    """

    # Called once to initialize an instance which lives until Plover exits
    def __init__(self, engine: StenoEngine) -> None:
        self._engine: StenoEngine = engine
        self._stenogotchiclient = StenogotchiClient(self)
        self._btclient = BTClient()
        self._wpm_meter = None
        self._strokes_meter = None
        self._output_to_stenogotchi = False

    # Started when user enables extension
    def start(self):
        """ Starts the server. """
        self._connect_hooks()
        plover.log.info("[stenogotchi_link] Plover_link started")
        self._stenogotchiclient.plover_is_running(True)

    # Called when Plover exits or user disables the extension
    def stop(self):
        """ Stops the server. """
        self._disconnect_hooks()
        self._stenogotchiclient.plover_is_running(False)

    def start_wpm_meter(self, enable_wpm=False, enable_strokes=False, wpm_method='ncra', wpm_timeout=60):
        """ Starts WPM and/or Strokes meters
        """
        if enable_wpm:
            self._wpm_meter = PloverWpmMeter(stenogotchi_link=self, wpm_method=wpm_method, timeout=wpm_timeout)
        if enable_strokes:
            self._strokes_meter = PloverStrokesMeter(stenogotchi_link=self, strokes_method=wpm_method, timeout=wpm_timeout)

    def stop_wpm_meter(self, disable_wpm=True, disable_strokes=True):
        if disable_wpm:
            self._wpm_meter.quit()
            self._wpm_meter = None
        if disable_strokes:
            self._strokes_meter.quit()
            self._strokes_meter = None

    def _on_wpm_meter_update_strokes(self, stats):
        """ Sends strokes stats to stenogotchi as a string """
        self._stenogotchiclient.plover_strokes_stats(stats['strokes_user'])

    def _on_wpm_meter_update_wpm(self, stats):
        """ Sends wpm stats to stenogotchi as a string """
        self._stenogotchiclient.plover_wpm_stats(stats['wpm_user'])

    def _on_plover_translation(self, results, type):
        """ Sends translation results from Plover to stenogotchi as list of strings"""
        if type == 'word':  # Result from Plover will be in format List[Tuple[str]], examine: {('EBGS', 'APL', '*EUPB'), ('KP*PL',), ('KPAPL', 'PHEUPB'), ('KPAPL', '-PB'), ('KP-PB',), ('EBGS', 'APL', '-PB'), ('KP',), ('EBGS', 'APL', 'PHEUPB'), ('EBGS', 'APL', 'EUPB')}
            results_list = []
            chords = None
            for touple in results:
                if chords:
                    results_list.append(chords)
                    chords = None
                for result in touple:
                    if chords:
                        chords = chords + '/' + result
                    else:
                        chords = result
            if chords:
                results_list.append(chords)
                chords = None
        elif type == 'stroke':  # Result from Plover will be in format str
            # TODO: implement functionality for stroke-lookup
            plover.log.debug(f"Lookup_stroke results: {results}")
            results_list = [results]
        self._stenogotchiclient.send_lookup_results(results_list)
    
    def lookup_word(self, word):
        matches = self._engine.reverse_lookup(word)
        self._on_plover_translation(matches, 'word')

    def lookup_stroke(self, stroke):
        matches = self._engine.lookup(stroke)
        self._on_plover_translation(matches, 'stroke')

    def get_server_status(self):
        """Gets the status of the server.
        Returns: 
            The status of the server.
        """
        pass

    def _connect_hooks(self):
        """Creates hooks into all of Plover's events."""

        if not self._engine:
            plover.log.error(f'[stenogotchi_link] {ERROR_MISSING_ENGINE}')
            raise AssertionError(ERROR_MISSING_ENGINE)
            
        for hook in self._engine.HOOKS:
            callback = getattr(self, f'_on_{hook}')
            self._engine.hook_connect(hook, callback)

    def _disconnect_hooks(self):
        """Removes hooks from all of Plover's events."""
        
        if not self._engine:
            raise AssertionError(ERROR_MISSING_ENGINE)

        for hook in self._engine.HOOKS:
            callback = getattr(self, f'_on_{hook}')
            self._engine.hook_disconnect(hook, callback)
    
    def _on_stroked(self, stroke: Stroke):
        """ Broadcasts when a new stroke is performed. """
        
        pass

    def _on_translated(self, old: List[_Action], new: List[_Action]):
        """Broadcasts when a new translation occurs.
        Args:
            old: A list of the previous actions for the current translation.
            new: A list of the new actions for the current translation.
        """
        
        # Send to WPM meter if we have one
        if self._wpm_meter:
            self._wpm_meter.on_translation(old, new)
        # Send to Strokes meter if we have one
        if self._strokes_meter:
            self._strokes_meter.on_translation(old, new)

        # print(self._wpm_meter.get_stats())
        # print(self._strokes_meter.get_stats())

    def _on_machine_state_changed(self, machine_type: str, machine_state: str):
        """Broadcasts when the active machine state changes.
        Args:
            machine_type: The name of the active machine.
            machine_state: The new machine state. This should be one of the
                state constants listed in plover.machine.base.
        """
        
        self._stenogotchiclient.plover_machine_state("machine_type: " + machine_type + " machine_state: " + machine_state)

    def _on_output_changed(self, enabled: bool):
        """Broadcasts when the state of output changes.
        Args:
            enabled: If the output is now enabled or not.
        """

        data = {'output_changed': enabled}
        plover.log.debug(f'[stenogotchi_link] _on_output_changed data: {data}')
        self._stenogotchiclient.plover_output_enabled(enabled)
        

    def _on_config_changed(self, config_update: Config):
        """Broadcasts when the configuration changes.
        Args:
            config_update: An object containing the full configuration or a
                part of the configuration that was updated.
        """

        config_json = jsonpickle.encode(config_update, unpicklable=False)

        data = {'config_changed': json.loads(config_json)}
        plover.log.debug(f'[stenogotchi_link] _on_config_changed data: {data}')

    def _on_dictionaries_loaded(self, dictionaries: StenoDictionaryCollection):
        """Broadcasts when all of the dictionaries get loaded.
        Args:
            dictionaries: A collection of the dictionaries that loaded.
        """

        self._stenogotchiclient.plover_is_ready(True)

    def _on_send_string(self, text: str):
        """Broadcasts when a new string is output.
        Args:
            text: The string that was output.
        """
        if self._output_to_stenogotchi:
            self._stenogotchiclient.send_string(text)
        else:
            self._btclient.send_string(text)

    def _on_send_backspaces(self, count: int):
        """Broadcasts when backspaces are output.
        Args:
            count: The number of backspaces that were output.
        """
        if self._output_to_stenogotchi:
            self._stenogotchiclient.send_backspaces(count)
        else:
            self._btclient.send_backspaces(count)

    def _on_send_key_combination(self, combination: str):
        """Broadcasts when a key combination is output.
        Args:
            combination: A string representing a sequence of key combinations.
                Keys are represented by their names based on the OS-specific
                keyboard implementations in plover.oslayer.
        """
        if self._output_to_stenogotchi:
            self._stenogotchiclient.send_key_combination(combination)
        else:
            self._btclient.send_key_combination(combination)

    def _on_add_translation(self):
        """Broadcasts when the add translation tool is opened via a command."""

        data = {'add_translation': True}
        plover.log.debug(f'[stenogotchi_link] _on_add_translation data: {data}')
        
    def _on_focus(self):
        """Broadcasts when the main window is focused via a command."""

        data = {'focus': True}
        plover.log.debug(f'[stenogotchi_link] _on_focus data: {data}')

    def _on_configure(self):
        """Broadcasts when the configuration tool is opened via a command."""

        data = {'configure': True}
        plover.log.debug(f'[stenogotchi_link] _on_configure data: {data}')

    def _on_lookup(self):
        """Broadcasts when the lookup tool is opened via a command."""

        data = {'lookup': True}
        plover.log.debug(f'[stenogotchi_link] _on_lookup data: {data}')

    def _on_suggestions(self):
        """Broadcasts when the lookup tool is opened via a command."""

        data = {'suggestions': True}
        plover.log.debug(f'[stenogotchi_link] _on_lookup data: {data}')

    def _on_quit(self):
        """Broadcasts when the application is terminated.
        Can be either a full quit or a restart.
        """

        data = {'quit': True}
        plover.log.debug(f'[stenogotchi_link] _on_quit data: {data}')
        self._stenogotchiclient.plover_is_running(False)


if __name__ == '__main__':
    print("Please enable and run as Plover plugin")
