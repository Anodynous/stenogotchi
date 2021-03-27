#!/usr/bin/python3
import logging
import argparse
import time
import signal
import sys
import toml

import stenogotchi
from stenogotchi import utils
from stenogotchi.plugins import cmd as plugins_cmd
from stenogotchi import log
from stenogotchi import restart
from stenogotchi import fs
from stenogotchi.utils import DottedTomlEncoder


def do_clear(display):
    logging.info("clearing the display ...")
    display.clear()
    sys.exit(0)

def do_manual_mode(agent):
    logging.info("entering manual mode ...")

    agent.mode = 'manual'
    agent.last_session.parse(agent.view(), args.skip_session)
    if not args.skip_session:
        logging.info("the last session lasted %s" % (agent.last_session.duration_human))

    while True:
        display.on_manual_mode(agent.last_session)
        time.sleep(5)

def do_auto_mode(agent):
    logging.info("entering auto mode ...")

    agent.mode = 'auto'
    agent.start()

    while True:
        try:
            # This is the main loop. But we don't have any main duty outside interacting with plover and acting as ui.
            # Need to come up with some more dynamic way of triggering UI updates based on Plover/etc events
            time.sleep(300)
            agent._view.on_normal()
        except Exception as e:
            logging.exception("main loop exception (%s)", e)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser = plugins_cmd.add_parsers(parser)

    parser.add_argument('-C', '--config', action='store', dest='config', default='/etc/stenogotchi/default.toml',
                        help='Main configuration file.')
    parser.add_argument('-U', '--user-config', action='store', dest='user_config', default='/etc/stenogotchi/config.toml',
                        help='If this file exists, configuration will be merged and this will override default values.')

    parser.add_argument('--manual', dest="do_manual", action="store_true", default=False, help="Manual mode.")
    parser.add_argument('--skip-session', dest="skip_session", action="store_true", default=False,
                        help="Skip last session parsing in manual mode.")

    parser.add_argument('--clear', dest="do_clear", action="store_true", default=False,
                        help="Clear the ePaper display and exit.")

    parser.add_argument('--debug', dest="debug", action="store_true", default=False,
                        help="Enable debug logs.")

    parser.add_argument('--version', dest="version", action="store_true", default=False,
                        help="Print the version.")

    parser.add_argument('--print-config', dest="print_config", action="store_true", default=False,
                        help="Print the configuration.")

    args = parser.parse_args()


    if plugins_cmd.used_plugin_cmd(args):
        config = utils.load_config(args)
        log.setup_logging(args, config)
        rc = plugins_cmd.handle_cmd(args, config)
        sys.exit(rc)

    if args.version:
        print(stenogotchi.__version__)
        sys.exit(0)

    config = utils.load_config(args)

    if args.print_config:
        print(toml.dumps(config, encoder=DottedTomlEncoder()))
        sys.exit(0)

    from stenogotchi.agent import Agent
    from stenogotchi.ui import fonts
    from stenogotchi.ui.display import Display
    from stenogotchi import plugins

    stenogotchi.config = config
    fs.setup_mounts(config)
    log.setup_logging(args, config)
    fonts.init(config)

    stenogotchi.set_name(config['main']['name'])

    plugins.load(config)

    display = Display(config=config, state={'name': '%s>' % stenogotchi.name()})

    if args.do_clear:
        do_clear(display)
        sys.exit(0)

    agent = Agent(view=display, config=config)

    def usr1_handler(*unused):
        logging.info('Received USR1 singal. Restart process ...')
        restart("MANU" if args.do_manual else "AUTO")

    signal.signal(signal.SIGUSR1, usr1_handler)

    if args.do_manual:
        do_manual_mode(agent)
    else:
        do_auto_mode(agent)


