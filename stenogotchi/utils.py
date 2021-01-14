import logging
import glob
import os
import sys
import time

import json
import shutil
import toml
import sys
import re

from toml.encoder import TomlEncoder, _dump_str
from zipfile import ZipFile
from datetime import datetime


class DottedTomlEncoder(TomlEncoder):
    """
    Dumps the toml into the dotted-key format
    """

    def __init__(self, _dict=dict):
        super(DottedTomlEncoder, self).__init__(_dict)

    def dump_list(self, v):
        retval = "["
        # 1 line if its just 1 item; therefore no newline
        if len(v) > 1:
            retval += "\n"
        for u in v:
            retval += " " + str(self.dump_value(u)) + ",\n"
        # 1 line if its just 1 item; remove newline
        if len(v) <= 1:
            retval = retval.rstrip("\n")
        retval += "]"
        return retval

    def dump_sections(self, o, sup):
        retstr = ""
        pre = ""

        if sup:
            pre = sup + "."

        for section, value in o.items():
            section = str(section)
            qsection = section
            if not re.match(r'^[A-Za-z0-9_-]+$', section):
                qsection = _dump_str(section)
            if value is not None:
                if isinstance(value, dict):
                    toadd, _ = self.dump_sections(value, pre + qsection)
                    retstr += toadd
                    # separte sections
                    if not retstr.endswith('\n\n'):
                        retstr += '\n'
                else:
                    retstr += (pre + qsection + " = " +
                                str(self.dump_value(value)) + '\n')
        return (retstr, self._dict())

def parse_version(version):
    """
    Converts a version str to tuple, so that versions can be compared
    """
    return tuple(version.split('.'))

def download_file(url, destination, chunk_size=128):
    import requests
    resp = requests.get(url)
    resp.raise_for_status()

    with open(destination, 'wb') as fd:
        for chunk in resp.iter_content(chunk_size):
            fd.write(chunk)

def unzip(file, destination, strip_dirs=0):
    os.makedirs(destination, exist_ok=True)
    with ZipFile(file, 'r') as zip:
        if strip_dirs:
            for info in zip.infolist():
                new_filename = info.filename.split('/', maxsplit=strip_dirs)[strip_dirs]
                if new_filename:
                    info.filename = new_filename
                    zip.extract(info, destination)
        else:
            zip.extractall(destination)

# https://stackoverflow.com/questions/823196/yaml-merge-in-python
def merge_config(user, default):
    if isinstance(user, dict) and isinstance(default, dict):
        for k, v in default.items():
            if k not in user:
                user[k] = v
            else:
                user[k] = merge_config(user[k], v)
    return user

def load_configOLD(args):
    import stenogotchi
    config_file = os.path.join(os.path.dirname(stenogotchi.__file__), 'config.toml')
    config = None

    # load the config
    with open(config_file) as fp:
        config = toml.load(fp)

    # check if display is supported 
    if config['ui']['display']['type'] in ('waveshare2in13v2', 'ws_2', 'ws2', 'waveshare_2', 'waveshare2'):
        config['ui']['display']['type'] = 'waveshare_2'
    else:
        print("unsupported display type %s" % config['ui']['display']['type'])
        sys.exit(1)
    return config

def save_config(config, target):
    with open(target, 'wt') as fp:
        fp.write(toml.dumps(config, encoder=DottedTomlEncoder()))
    return True

def load_config(args):
    default_config_path = os.path.dirname(args.config)
    if not os.path.exists(default_config_path):
        os.makedirs(default_config_path)

    import stenogotchi
    ref_defaults_file = os.path.join(os.path.dirname(stenogotchi.__file__), 'defaults.toml')
    ref_defaults_data = None

    # check for a config.toml file on /boot/
    boot_conf = '/boot/config.toml'
    if os.path.exists(boot_conf):
        # logging not configured here yet
        print("installing %s to %s ...", boot_conf, args.user_config)
        # https://stackoverflow.com/questions/42392600/oserror-errno-18-invalid-cross-device-link
        shutil.move(boot_conf, args.user_config)

    # check for an entire stenogotchi folder on /boot/
    if os.path.isdir('/boot/stenogotchi'):
        print("installing /boot/stenogotchi to /etc/stenogotchi ...")
        shutil.rmtree('/etc/stenogotchi', ignore_errors=True)
        shutil.move('/boot/stenogotchi', '/etc/')

    # if not config is found, copy the defaults
    if not os.path.exists(args.config):
        print("copying %s to %s ..." % (ref_defaults_file, args.config))
        shutil.copy(ref_defaults_file, args.config)
    else:
        # check if the user messed with the defaults

        with open(ref_defaults_file) as fp:
            ref_defaults_data = fp.read()

        with open(args.config) as fp:
            defaults_data = fp.read()

        if ref_defaults_data != defaults_data:
            print("!!! file in %s is different than release defaults, overwriting !!!" % args.config)
            shutil.copy(ref_defaults_file, args.config)

    # load the defaults
    with open(args.config) as fp:
        config = toml.load(fp)

    # load the user config
    try:
        user_config = None
        if os.path.exists(args.user_config):
            with open(args.user_config) as toml_file:
                user_config = toml.load(toml_file)

        if user_config:
            config = merge_config(user_config, config)
    except Exception as ex:
        logging.error("There was an error processing the configuration file:\n%s ",ex)
        sys.exit(1)

    # dropins
    dropin = config['main']['confd']
    if dropin and os.path.isdir(dropin):
        dropin += '*.toml' if dropin.endswith('/') else '/*.toml'
        for conf in glob.glob(dropin):
            with open(conf) as toml_file:
                additional_config = toml.load(toml_file)
                config = merge_config(additional_config, config)

    # the very first step is to normalize the display name so we don't need dozens of if/elif around
    #if config['ui']['display']['type'] in ('inky', 'inkyphat'):
    #    config['ui']['display']['type'] = 'inky'

    #elif config['ui']['display']['type'] in ('papirus', 'papi'):
    #    config['ui']['display']['type'] = 'papirus'

    #elif config['ui']['display']['type'] in ('oledhat',):
    #    config['ui']['display']['type'] = 'oledhat'

    #elif config['ui']['display']['type'] in ('ws_1', 'ws1', 'waveshare_1', 'waveshare1'):
    #    config['ui']['display']['type'] = 'waveshare_1'

    if config['ui']['display']['type'] in ('ws_2', 'ws2', 'waveshare_2', 'waveshare2', 'waveshare2in13v2'):
        config['ui']['display']['type'] = 'waveshare_2'

    #elif config['ui']['display']['type'] in ('ws_27inch', 'ws27inch', 'waveshare_27inch', 'waveshare27inch'):
    #    config['ui']['display']['type'] = 'waveshare27inch'

    #elif config['ui']['display']['type'] in ('ws_29inch', 'ws29inch', 'waveshare_29inch', 'waveshare29inch'):
    #    config['ui']['display']['type'] = 'waveshare29inch'

    #elif config['ui']['display']['type'] in ('lcdhat',):
    #    config['ui']['display']['type'] = 'lcdhat'

    #elif config['ui']['display']['type'] in ('dfrobot_1', 'df1'):
    #    config['ui']['display']['type'] = 'dfrobot_1'

    #elif config['ui']['display']['type'] in ('dfrobot_2', 'df2'):
    #    config['ui']['display']['type'] = 'dfrobot_2'

    #elif config['ui']['display']['type'] in ('ws_154inch', 'ws154inch', 'waveshare_154inch', 'waveshare154inch'):
    #    config['ui']['display']['type'] = 'waveshare154inch'

    #elif config['ui']['display']['type'] in ('waveshare144lcd', 'ws_144inch', 'ws144inch', 'waveshare_144inch', 'waveshare144inch'):
    #    config['ui']['display']['type'] = 'waveshare144lcd'

    #elif config['ui']['display']['type'] in ('ws_213d', 'ws213d', 'waveshare_213d', 'waveshare213d'):
    #    config['ui']['display']['type'] = 'waveshare213d'

    #elif config['ui']['display']['type'] in ('ws_213bc', 'ws213bc', 'waveshare_213bc', 'waveshare213bc'):
    #    config['ui']['display']['type'] = 'waveshare213bc'

    #elif config['ui']['display']['type'] in ('spotpear24inch'):
    #    config['ui']['display']['type'] = 'spotpear24inch'

    else:
        print("unsupported display type %s" % config['ui']['display']['type'])
        sys.exit(1)

    return config

def secs_to_hhmmss(secs):
    mins, secs = divmod(secs, 60)
    hours, mins = divmod(mins, 60)
    return '%02d:%02d:%02d' % (hours, mins, secs)

def led(on=True):
    with open('/sys/class/leds/led0/brightness', 'w+t') as fp:
        fp.write("%d" % (0 if on is True else 1))


def blink(times=1, delay=0.3):
    for _ in range(0, times):
        led(True)
        time.sleep(delay)
        led(False)
        time.sleep(delay)
    led(True)

class StatusFile(object):
    def __init__(self, path, data_format='raw'):
        self._path = path
        self._updated = None
        self._format = data_format
        self.data = None

        if os.path.exists(path):
            self._updated = datetime.fromtimestamp(os.path.getmtime(path))
            with open(path) as fp:
                if data_format == 'json':
                    self.data = json.load(fp)
                else:
                    self.data = fp.read()

    def data_field_or(self, name, default=""):
        if self.data is not None and name in self.data:
            return self.data[name]
        return default

    def newer_then_minutes(self, minutes):
        return self._updated is not None and ((datetime.now() - self._updated).seconds / 60) < minutes

    def newer_then_hours(self, hours):
        return self._updated is not None and ((datetime.now() - self._updated).seconds / (60 * 60)) < hours

    def newer_then_days(self, days):
        return self._updated is not None and (datetime.now() - self._updated).days < days

    def update(self, data=None):
        from stenogotchi.fs import ensure_write
        self._updated = datetime.now()
        self.data = data
        with ensure_write(self._path, 'w') as fp:
            if data is None:
                fp.write(str(self._updated))

            elif self._format == 'json':
                json.dump(self.data, fp)

            else:
                fp.write(data)