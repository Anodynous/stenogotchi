#!/usr/bin/env python3
# This is a Plover plugin acting as link between Plover and Stenogotchi
# Based on: https://github.com/nsmarkop/plover_websocket_server

import logging
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

ERROR_MISSING_ENGINE = 'Plover engine not provided'


class EngineServer():
    """
    Hooks into Plover events and makes them available to Stenogotchi.
    """

    # Called once to initialize an instance which lives until Plover exits
    def __init__(self, engine: StenoEngine) -> None:
        self._engine: StenoEngine = engine
        self._btclient = BTClient()
        self._stenogotchiclient = StenogotchiClient()

    # Started when user enables extension
    def start(self):
        """ Starts the server. """
        self._connect_hooks()
        logging.debug("Plover_link started")
        self._stenogotchiclient.plover_is_running(True)

    # Called when Plover exits or user disables the extension
    def stop(self):
        """ Stops the server. """
        self._disconnect_hooks()
        self._stenogotchiclient.plover_is_running(False)

    def get_server_status(self):
        """Gets the status of the server.
        Returns: 
            The status of the server.
        """
        pass

    def _connect_hooks(self):
        """Creates hooks into all of Plover's events."""

        if not self._engine:
            logging.debug(ERROR_MISSING_ENGINE)
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

        logging.debug(stroke)

    def _on_translated(self, old: List[_Action], new: List[_Action]):
        """Broadcasts when a new translation occurs.
        Args:
            old: A list of the previous actions for the current translation.
            new: A list of the new actions for the current translation.
        """

        old_json = jsonpickle.encode(old, unpicklable=False)
        new_json = jsonpickle.encode(new, unpicklable=False)

        data = {
            'translated': {
                'old': json.loads(old_json),
                'new': json.loads(new_json)
            }
        }
        logging.debug(data)

    def _on_machine_state_changed(self, machine_type: str, machine_state: str):
        """Broadcasts when the active machine state changes.
        Args:
            machine_type: The name of the active machine.
            machine_state: The new machine state. This should be one of the
                state constants listed in plover.machine.base.
        """
        
        data = {
            'machine_state_changed': {
                'machine_type': machine_type,
                'machine_state': machine_state
            }
        }
        logging.debug(data)
        self._stenogotchiclient.plover_machine_state("machine_type: " + machine_type + " machine_state: " + machine_state)

    def _on_output_changed(self, enabled: bool):
        """Broadcasts when the state of output changes.
        Args:
            enabled: If the output is now enabled or not.
        """

        data = {'output_changed': enabled}
        logging.debug(data)
        self._stenogotchiclient.plover_output_enabled(enabled)
        

    def _on_config_changed(self, config_update: Config):
        """Broadcasts when the configuration changes.
        Args:
            config_update: An object containing the full configuration or a
                part of the configuration that was updated.
        """

        config_json = jsonpickle.encode(config_update, unpicklable=False)

        data = {'config_changed': json.loads(config_json)}
        logging.debug(data)

    def _on_dictionaries_loaded(self, dictionaries: StenoDictionaryCollection):
        """Broadcasts when all of the dictionaries get loaded.
        Args:
            dictionaries: A collection of the dictionaries that loaded.
        """

        #dictionaries_json = jsonpickle.encode(dictionaries, unpicklable=False)
        #data = {'dictionaries_loaded': json.loads(dictionaries_json)}
        #logging.debug(data)
        self._stenogotchiclient.plover_is_ready(True)

    def _on_send_string(self, text: str):
        """Broadcasts when a new string is output.
        Args:
            text: The string that was output.
        """

        data = {'send_string': text}
        logging.debug(data)
        self._btclient.send_string(text)

    def _on_send_backspaces(self, count: int):
        """Broadcasts when backspaces are output.
        Args:
            count: The number of backspaces that were output.
        """

        data = {'send_backspaces': count}
        logging.debug(data)
        self._btclient.send_backspaces(count)

    def _on_send_key_combination(self, combination: str):
        """Broadcasts when a key combination is output.
        Args:
            combination: A string representing a sequence of key combinations.
                Keys are represented by their names based on the OS-specific
                keyboard implementations in plover.oslayer.
        """

        data = {'send_key_combination': combination}
        logging.debug(data)

    def _on_add_translation(self):
        """Broadcasts when the add translation tool is opened via a command."""

        data = {'add_translation': True}
        logging.debug(data)
        
    def _on_focus(self):
        """Broadcasts when the main window is focused via a command."""

        data = {'focus': True}
        logging.debug(data)

    def _on_configure(self):
        """Broadcasts when the configuration tool is opened via a command."""

        data = {'configure': True}
        logging.debug(data)

    def _on_lookup(self):
        """Broadcasts when the lookup tool is opened via a command."""

        data = {'lookup': True}
        logging.debug(data)

    def _on_quit(self):
        """Broadcasts when the application is terminated.
        Can be either a full quit or a restart.
        """

        data = {'quit': True}
        logging.debug(data)
        self._stenogotchiclient.plover_is_running(False)

if __name__ == '__main__':
    print("Run as a Plover plugin to enable functionality.")
