import logging
import os
import _thread
import secrets
import subprocess
from functools import wraps

# https://stackoverflow.com/questions/14888799/disable-console-messages-in-flask-server
logging.getLogger('werkzeug').setLevel(logging.ERROR)
os.environ['WERKZEUG_RUN_MAIN'] = 'true'

import stenogotchi
import stenogotchi.ui.web as web
from stenogotchi import plugins

from flask import send_file
from flask import Response
from flask import request
from flask import abort
from flask import redirect
from flask import render_template, render_template_string


class Handler:
    def __init__(self, config, agent, app):
        self._config = config
        self._agent = agent
        self._app = app

        self._app.add_url_rule('/', 'index', self.with_auth(self.index))
        self._app.add_url_rule('/ui', 'ui', self.with_auth(self.ui))

        self._app.add_url_rule('/shutdown', 'shutdown', self.with_auth(self.shutdown), methods=['POST'])
        
        self._app.add_url_rule('/toggle_input', 'toggle_input', self.with_auth(self.toggle_input), methods=['POST'])
        self._app.add_url_rule('/toggle_wpm', 'toggle_wpm', self.with_auth(self.toggle_wpm), methods=['POST'])
        self._app.add_url_rule('/reset_plover', 'reset_plover', self.with_auth(self.reset_plover), methods=['POST'])
        self._app.add_url_rule('/buttonshim/<button>', 'buttonshim', self.with_auth(self.buttonshim), methods=['GET'])

        self._app.add_url_rule('/reboot', 'reboot', self.with_auth(self.reboot), methods=['POST'])
        self._app.add_url_rule('/restart', 'restart', self.with_auth(self.restart), methods=['POST'])

        # plugins
        plugins_with_auth = self.with_auth(self.plugins)
        self._app.add_url_rule('/plugins', 'plugins', plugins_with_auth, strict_slashes=False,
                               defaults={'name': None, 'subpath': None})
        self._app.add_url_rule('/plugins/<name>', 'plugins', plugins_with_auth, strict_slashes=False,
                               methods=['GET', 'POST'], defaults={'subpath': None})
        self._app.add_url_rule('/plugins/<name>/<path:subpath>', 'plugins', plugins_with_auth, methods=['GET', 'POST'])

    def _check_creds(self, u, p):
        # trying to be timing attack safe
        return secrets.compare_digest(u, self._config['username']) and \
               secrets.compare_digest(p, self._config['password'])

    def with_auth(self, f):
        @wraps(f)
        def wrapper(*args, **kwargs):
            auth = request.authorization
            if not auth or not auth.username or not auth.password or not self._check_creds(auth.username,
                                                                                           auth.password):
                return Response('Unauthorized', 401, {'WWW-Authenticate': 'Basic realm="Unauthorized"'})
            return f(*args, **kwargs)

        return wrapper

    def index(self):
        return render_template('index.html',
                               title=stenogotchi.name(),
                               other_mode='AUTO' if self._agent.mode == 'manual' else 'MANU')

    def plugins(self, name, subpath):
        if name is None:
            return render_template('plugins.html', loaded=plugins.loaded, database=plugins.database)

        if name == 'toggle' and request.method == 'POST':
            checked = True if 'enabled' in request.form else False
            return 'success' if plugins.toggle_plugin(request.form['plugin'], checked) else 'failed'

        if name in plugins.loaded and plugins.loaded[name] is not None and hasattr(plugins.loaded[name], 'on_webhook'):
            try:
                return plugins.loaded[name].on_webhook(subpath, request)
            except Exception:
                abort(500)
        else:
            abort(404)

    # serve a message and shuts down the unit
    def shutdown(self):
        try:
            return render_template('status.html', title=stenogotchi.name(), go_back_after=60,
                                   message='Shutting down ...')
        finally:
            _thread.start_new_thread(stenogotchi.shutdown, ())

    # switch between STENO and QWERTY input mode
    def toggle_input(self):
        if 'buttonshim' in plugins.loaded:
            _thread.start_new_thread(plugins.loaded['buttonshim'].toggle_qwerty_steno, ())
            return redirect("/")
        else:
            return render_template('status.html', title=stenogotchi.name(), go_back_after=10,
                                   message='Please enable the buttonshim plugin first.')

    # toggle WPM readings
    def toggle_wpm(self):
        if 'buttonshim' in plugins.loaded:
            _thread.start_new_thread(plugins.loaded['buttonshim'].toggle_wpm_meters, ())
            return redirect("/")
        else: 
            return render_template('status.html', title=stenogotchi.name(), go_back_after=10,
                                message='Please enable the buttonshim plugin first.')
    
    # reset plover
    def reset_plover(self):
        command = {'reset_plover': True}
        _thread.start_new_thread(plugins.loaded['plover_link'].send_signal_to_plover, (command,))
        logging.info("[WEBUI] Sent machine reset command to Plover")
        return redirect("/")
    
    # buttonshim custom action (emulating buttonshim short press)
    def buttonshim(self, button):
        logging.info(f"[WEBUI-buttonshim] Button Pressed! Loading command from slot '{button}' for button '{button}'")
        bCfg = plugins.loaded['buttonshim'].options['buttons'][button]
        command = bCfg['command']
        if command == '':
            logging.debug(f"[WEBUI-buttonshim] No command set for button {button} in config")
            return render_template('status.html', title=stenogotchi.name(), go_back_after=5, 
                                    message=f"No command set in config for button {button}")
        else:
            logging.debug(f"[WEBUI-buttonshim] Process create: {command}")
            process = subprocess.Popen(command, shell=True, stdin=None, 
                                        stdout=open("/dev/null", "w"), stderr=None, executable="/bin/bash")
            process.wait()
            process = None
            logging.debug(f"[WEBUI-buttonshim] Process end")
            return render_template('status.html', title=stenogotchi.name(), go_back_after=10, 
                                    message=f"Executed command: '{command}'")
        
    # serve a message and reboot the unit
    def reboot(self):
          try:
              return render_template('status.html', title=stenogotchi.name(), go_back_after=70,
                                     message='Rebooting ...')
          finally:
              _thread.start_new_thread(stenogotchi.reboot, ())

    # serve a message and restart the unit in the other mode
    def restart(self):
        mode = request.form['mode']
        if mode not in ('AUTO', 'MANU'):
            mode = 'MANU'

        try:
            return render_template('status.html', title=stenogotchi.name(), go_back_after=30,
                                   message='Restarting in %s mode ...' % mode)
        finally:
            _thread.start_new_thread(stenogotchi.restart, (mode,))

    # serve the PNG file with the display image
    def ui(self):
        with web.frame_lock:
            return send_file(web.frame_path, mimetype='image/png')
