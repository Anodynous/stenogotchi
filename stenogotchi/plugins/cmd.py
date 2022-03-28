# Handles the commandline stuff

import os
import logging
import glob
import re
import shutil
from fnmatch import fnmatch
from stenogotchi.plugins import default_path


SAVE_DIR = '/usr/local/share/stenogotchi/availaible-plugins/'
DEFAULT_INSTALL_PATH = '/usr/local/share/stenogotchi/installed-plugins/'


def add_parsers(parser):
    """
    Adds the plugins subcommand to a given argparse.ArgumentParser
    """
    subparsers = parser.add_subparsers()
    ## stenogotchi plugins
    parser_plugins = subparsers.add_parser('plugins')
    plugin_subparsers = parser_plugins.add_subparsers(dest='plugincmd')

    ## stenogotchi plugins search
    parser_plugins_search = plugin_subparsers.add_parser('search', help='Search for stenogotchi plugins')
    parser_plugins_search.add_argument('pattern', type=str, help="Search expression (wildcards allowed)")

    ## stenogotchi plugins list
    parser_plugins_list = plugin_subparsers.add_parser('list', help='List available stenogotchi plugins')
    parser_plugins_list.add_argument('-i', '--installed', action='store_true', required=False, help='List also installed plugins')

    ## stenogotchi plugins update
    parser_plugins_update = plugin_subparsers.add_parser('update', help='Updates the database')

    ## stenogotchi plugins upgrade
    parser_plugins_upgrade = plugin_subparsers.add_parser('upgrade', help='Upgrades plugins')
    parser_plugins_upgrade.add_argument('pattern', type=str, nargs='?', default='*', help="Filter expression (wildcards allowed)")

    ## stenogotchi plugins enable
    parser_plugins_enable = plugin_subparsers.add_parser('enable', help='Enables a plugin')
    parser_plugins_enable.add_argument('name', type=str, help='Name of the plugin')

    ## stenogotchi plugins disable
    parser_plugins_disable = plugin_subparsers.add_parser('disable', help='Disables a plugin')
    parser_plugins_disable.add_argument('name', type=str, help='Name of the plugin')

    ## stenogotchi plugins install
    parser_plugins_install = plugin_subparsers.add_parser('install', help='Installs a plugin')
    parser_plugins_install.add_argument('name', type=str, help='Name of the plugin')

    ## stenogotchi plugins uninstall
    parser_plugins_uninstall = plugin_subparsers.add_parser('uninstall', help='Uninstalls a plugin')
    parser_plugins_uninstall.add_argument('name', type=str, help='Name of the plugin')

    ## stenogotchi plugins edit
    parser_plugins_edit = plugin_subparsers.add_parser('edit', help='Edit the options')
    parser_plugins_edit.add_argument('name', type=str, help='Name of the plugin')

    return parser


def used_plugin_cmd(args):
    """
    Checks if the plugins subcommand was used
    """
    return hasattr(args, 'plugincmd')


def handle_cmd(args, config):
    """
    Parses the arguments and does the thing the user wants
    """
    if args.plugincmd == 'update':
        return update(config)
    elif args.plugincmd == 'search':
        args.installed = True # also search in installed plugins
        return list_plugins(args, config, args.pattern)
    elif args.plugincmd == 'install':
        return install(args, config)
    elif args.plugincmd == 'uninstall':
        return uninstall(args, config)
    elif args.plugincmd == 'list':
        return list_plugins(args, config)
    elif args.plugincmd == 'enable':
        return enable(args, config)
    elif args.plugincmd == 'disable':
        return disable(args, config)
    elif args.plugincmd == 'upgrade':
        return upgrade(args, config, args.pattern)
    elif args.plugincmd == 'edit':
        return edit(args, config)

    raise NotImplementedError()


def edit(args, config):
    pass


def enable(args, config):
    pass


def disable(args, config):
    pass


def upgrade(args, config, pattern='*'):
    pass

def list_plugins(args, config, pattern='*'):
    """
    Lists the available and installed plugins
    """
    installed = _get_installed(config)
    print(installed)
    return 0


def _extract_version(filename):
    """
    Extracts the version from a python file
    """
    return None


def _get_available():
    """
    Get all availaible plugins
    """
    return None


def _get_installed(config):
    """
    Get all installed plugins
    """
    installed = dict()
    search_dirs = [ default_path, config['main']['custom_plugins'] ]
    for search_dir in search_dirs:
        if search_dir:
            for filename in glob.glob(os.path.join(search_dir, "*.py")):
                plugin_name = os.path.basename(filename.replace(".py", ""))
                installed[plugin_name] = filename
    return installed


def uninstall(args, config):
    """
    Uninstalls a plugin
    """
    return 0


def install(args, config):
    """
    Installs the given plugin
    """
    return 0


def _analyse_dir(path):
    return None


def update(config):
    """
    Updates the database
    """
    return 0