import os
import glob
import _thread
import threading
import importlib, importlib.util
import logging



default_path = os.path.join(os.path.dirname(os.path.realpath(__file__)), "default")
loaded = {}
database = {}
locks = {}


class Plugin:
    @classmethod
    def __init_subclass__(cls, **kwargs):
        super().__init_subclass__(**kwargs)
        global loaded, locks

        plugin_name = cls.__module__.split('.')[0]
        plugin_instance = cls()
        logging.debug("loaded plugin %s as %s" % (plugin_name, plugin_instance))
        loaded[plugin_name] = plugin_instance

        for attr_name in plugin_instance.__dir__():
            if attr_name.startswith('on_'):
                cb = getattr(plugin_instance, attr_name, None)
                if cb is not None and callable(cb):
                    locks["%s::%s" % (plugin_name, attr_name)] = threading.Lock()


def toggle_plugin(name, enable=True):
    """
    Load or unload a plugin
    returns True if changed, otherwise False
    """
    import stenogotchi
    from stenogotchi.ui import view
    from stenogotchi.utils import save_config
  
    global loaded, database

    # log event
    if enable:
        logging.debug(f"enabled plugin '{name}' in config")
    else:
        logging.debug(f"disabled plugin '{name}' in config")

    if stenogotchi.config:
        if not name in stenogotchi.config['main']['plugins']:
            stenogotchi.config['main']['plugins'][name] = dict()
        stenogotchi.config['main']['plugins'][name]['enabled'] = enable
        save_config(stenogotchi.config, '/etc/stenogotchi/config.toml')

    if not enable and name in loaded:
        if getattr(loaded[name], 'on_unload', None):
            loaded[name].on_unload(view.ROOT)
        del loaded[name]

        return True

    if enable and name in database and name not in loaded:
        load_from_file(database[name])
        if name in loaded and stenogotchi.config and name in stenogotchi.config['main']['plugins']:
            loaded[name].options = stenogotchi.config['main']['plugins'][name]
        one(name, 'loaded')
        if stenogotchi.config:
            one(name, 'config_changed', stenogotchi.config)
        one(name, 'ui_setup', view.ROOT)
        one(name, 'ready', view.ROOT._agent)
        return True

    return False


def on(event_name, *args, **kwargs):
    for plugin_name in loaded.keys():
        one(plugin_name, event_name, *args, **kwargs)


def locked_cb(lock_name, cb, *args, **kwargs):
    global locks

    if lock_name not in locks:
        locks[lock_name] = threading.Lock()

    with locks[lock_name]:
        cb(*args, *kwargs)


def one(plugin_name, event_name, *args, **kwargs):
    global loaded

    if plugin_name in loaded:
        plugin = loaded[plugin_name]
        cb_name = 'on_%s' % event_name
        callback = getattr(plugin, cb_name, None)
        if callback is not None and callable(callback):
            try:
                lock_name = "%s::%s" % (plugin_name, cb_name)
                locked_cb_args = (lock_name, callback, *args, *kwargs)
                _thread.start_new_thread(locked_cb, locked_cb_args)
            except Exception as e:
                logging.error("error while running %s.%s : %s" % (plugin_name, cb_name, e))
                logging.error(e, exc_info=True)


def load_from_file(filename):
    logging.debug("loading %s" % filename)
    plugin_name = os.path.basename(filename.replace(".py", ""))
    spec = importlib.util.spec_from_file_location(plugin_name, filename)
    instance = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(instance)
    return plugin_name, instance


def load_from_path(path, enabled=()):
    global loaded, database
    logging.debug("loading plugins from %s - enabled: %s" % (path, enabled))
    for filename in glob.glob(os.path.join(path, "*.py")):
        plugin_name = os.path.basename(filename.replace(".py", ""))
        database[plugin_name] = filename
        if plugin_name in enabled:
            try:
                load_from_file(filename)
            except Exception as e:
                logging.warning("error while loading %s: %s" % (filename, e))
                logging.debug(e, exc_info=True)

    return loaded


def load(config):
    enabled = [name for name, options in config['main']['plugins'].items() if
               'enabled' in options and options['enabled']]
    
    # force enable buttonshim plugin when web ui is enabled
    logging.debug(f"REMOVEME pre status : '{enabled}'")
    if config['ui']['web']['enabled'] and 'buttonshim' not in enabled:
        enabled.append('buttonshim')
    logging.debug(f"REMOVEME post status : '{enabled}'")

    # load default plugins
    load_from_path(default_path, enabled=enabled)

    # load custom ones
    custom_path = config['main']['custom_plugins'] if 'custom_plugins' in config['main'] else None
    if custom_path is not None:
        load_from_path(custom_path, enabled=enabled)

    # propagate options
    for name, plugin in loaded.items():
        plugin.options = config['main']['plugins'][name]
        print("loaded plugin:", name, plugin)

    on('loaded')
    on('config_changed', config)