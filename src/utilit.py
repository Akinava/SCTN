# -*- coding: utf-8 -*-
import json
import os
import sys
import logging
import pycrypto
import settings


__author__ = 'Akinava'
__author_email__ = 'akinava@gmail.com'
__copyright__ = "Copyright © 2019"
__license__ = "MIT License"
__version__ = [0, 0]


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


def pack_peers():
    peers_for_file = {}
    for fingerprint in settings.peers:
        fingerprint_b58 = pycrypto.B58().pack(fingerprint)
        peers_for_file[fingerprint_b58] = settings.peers[fingerprint]
    return peers_for_file


def unpack_peers(data):
    if not hasattr(settings, 'peers'):
        settings.peers = {}
    peers_from_file = json.loads(data)
    for fingerprint_b58 in peers_from_file:
        fingerprint = pycrypto.B58().unpack(fingerprint_b58)
        settings.peers[fingerprint] = peers_from_file[fingerprint_b58]


def import_config():
    with open(settings.config_file, 'r') as cfg_file:
        config = json.loads(cfg_file.read())
        for k, v in config.items():
            setattr(settings, k, v)


def import_peers():
    if os.path.isfile(settings.peers_file):
        with open(settings.peers_file, 'r') as f:
            try:
                unpack_peers(f.read())
            except json.decoder.JSONDecodeError:
                settings.logger.error('cannot parse peers file')
    else:
        settings.peers = {}


def add_peer(peer):
    peer_data = {peer['fingerprint']:
                 {'ip': peer['ip'],
                  'port': peer['port']}}
    if peer.get('signal'):
        peer_data[peer['fingerprint']]['signal'] = True
    settings.peers.update(peer_data)
    save_peers()


def save_peers():
    with open(settings.peers_file, 'w') as f:
        f.write(json.dumps(pack_peers(), indent=2))


def setup_settings():
    setup_logger()
    import_config()
    import_peers()


settings.add_peer = add_peer
