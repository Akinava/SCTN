# -*- coding: utf-8 -*-
__author__ = 'Akinava'
__author_email__ = 'akinava@gmail.com'
__copyright__ = 'Copyright © 2019'
__license__ = 'MIT License'
__version__ = [0, 0]


import json
import sys
import random
import struct
import logging
import settings
import get_args
from cryptotool import *


class Singleton(object):
    def __new__(cls):
        if not hasattr(cls, '_instance'):
            cls._instance = super(Singleton, cls).__new__(cls)
        return cls._instance


def setup_logger():
    settings.logger = logging.getLogger(__name__)
    settings.logger.setLevel(settings.logging_level)
    handler = logging.StreamHandler(sys.stdout)
    formatter = logging.Formatter(settings.logging_format)
    handler.setFormatter(formatter)
    settings.logger.addHandler(handler)


def read_config_file():
    with open(settings.config_file, 'r') as cfg_file:
        return json.loads(cfg_file.read())


def import_config():
    options, args = get_args.parser()
    options_items = vars(options)
    config = read_config_file()
    for k, v in config.items():
        if k in options_items and not getattr(options, k) is None:
            continue
        setattr(settings, k, v)


def import_options():
    options, args = get_args.parser()
    for key in vars(options):
        value = getattr(options, key)
        if value is None:
            continue
        setattr(settings, key, value)


def setup_settings():
    setup_logger()
    import_options()
    import_config()


def get_random_server_from_file():
    peers = read_peers_from_file()
    servers = filter_peers(peers, 'server')
    if not servers:
        return None
    return random.choice(servers)


def filter_peers(peers, filter):
    filtered_peers = []
    for peer in peers:
        if peer['type'] != filter:
            continue
        filtered_peers.append(peer)
    return filtered_peers


def read_peers_from_file():
    with open(settings.peers_file, 'r') as f:
        peers_list = json.loads(f.read())
        return unpack_peers_fingerprint(peers_list)

def unpack_peers_fingerprint(peers_list):
    for peer_index in range(len(peers_list)):
        peer = peers_list[peer_index]
        peer['fingerprint'] = B58().unpack(peer['fingerprint'])
    return peers_list


def pack_host(host):
    return ''.join(map(chr, (map(int, map(str, host.split('.')))))).encode()


def pack_port(port):
    return struct.pack('H', port)


def unpack_stream(data, length):
    return data[ :length], data[length: ]


def encode(text):
    if isinstance(text, str):
        return text.encode()
    if isinstance(bytes, str):
        return text
    raise Exception('Error: can\' encode, twrong type is {}'.format(type(text)))
