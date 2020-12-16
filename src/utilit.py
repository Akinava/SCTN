# -*- coding: utf-8 -*-
import json
import os
import sys
import logging
import settings
import connections


__author__ = 'Akinava'
__author_email__ = 'akinava@gmail.com'
__copyright__ = "Copyright © 2019"
__license__ = "MIT License"
__version__ = [0, 0]

# FIXME

def setup_logger():
    settings.logger = logging.getLogger(__name__)
    settings.logger.setLevel(settings.logging_level)
    handler = logging.StreamHandler(sys.stdout)
    formatter = logging.Formatter(settings.logging_format)
    handler.setFormatter(formatter)
    settings.logger.addHandler(handler)


def say_in_place(x, y, text):
    sys.stdout.write("\x1b7\x1b[{};{}f{}\x1b8".format(x, y, text))
    sys.stdout.flush()


def import_config():
    settings.path = os.path.dirname(os.path.abspath(__file__))
    with open(os.path.join(settings.path, settings.config_file), 'r') as cfg_file:
        config = json.loads(cfg_file.read())
        for k, v in config.items():
            setattr(settings, k, v)


def setup_settings():
    setup_logger()
    import_config()


def import_peers():
    peers = connections.Peers()
    connections.peers = peers


def init_connections():
    connections_list = connections.Connections()
    connections.connections = connections_list


def setup_connections():
    import_peers()
    init_connections()