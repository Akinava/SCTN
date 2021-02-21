# -*- coding: utf-8 -*-
__author__ = 'Akinava'
__author_email__ = 'akinava@gmail.com'
__copyright__ = 'Copyright © 2019'
__license__ = 'MIT License'
__version__ = [0, 0]


import json
import os
import sys
import logging
import settings
import getopt


def setup_logger():
    settings.logger = logging.getLogger(__name__)
    settings.logger.setLevel(settings.logging_level)
    handler = logging.StreamHandler(sys.stdout)
    formatter = logging.Formatter(settings.logging_format)
    handler.setFormatter(formatter)
    settings.logger.addHandler(handler)


def import_config():
    settings.path = os.path.dirname(os.path.abspath(__file__))
    with open(os.path.join(settings.path, settings.config_file), 'r') as cfg_file:
        config = json.loads(cfg_file.read())
        for k, v in config.items():
            setattr(settings, k, v)


def import_options():
    options, args = getopt.parser()
    for key in vars(options):
        value = getattr(options, key)
        if value is None:
            continue
        setattr(settings, key, value)



def setup_settings():
    setup_logger()
    import_config()
    import_options()
