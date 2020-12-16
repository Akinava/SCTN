# -*- coding: utf-8 -*-
import pycrypto

# FIXME

__author__ = 'Akinava'
__author_email__ = 'akinava@gmail.com'
__copyright__ = "Copyright © 2019"
__license__ = "MIT License"
__version__ = [0, 0]


class Connections:
    _instance = None

    def __new__(class_, *args, **kwargs):
        if not isinstance(class_._instance, class_):
            class_._instance = object.__new__(class_, *args, **kwargs)
        return class_._instance


class Connection:
    def __init__(self, peer=None):
        pass


class Peers:
    def __init__(self):
        self.__swarm = []
        self.__sstn = []
        self.__import_peers()

    def __import_peers(self):
        peers_file = os.path.join(file_dir, settings.peers_file)
        if os.path.isfile(peers_file):
            with open(peers_file, 'r') as f:
                try:
                    unpack_peers(f.read())
                except json.decoder.JSONDecodeError:
                    settings.logger.error('cannot parse peers file')
        else:
            settings.peers = {}




    def get_rundom_sstn_peer(self):
        pass


def import_peers():


def add_peer(peer):
    peer_data = {peer['fingerprint']:
                     {'ip': peer['ip'],
                      'port': peer['port']}}
    if peer.get('signal'):
        peer_data[peer['fingerprint']]['signal'] = True
    settings.peers.update(peer_data)
    save_peers()


def save_peers():
    peers_file = os.path.join(file_dir, settings.peers_file)
    with open(peers_file, 'w') as f:
        f.write(json.dumps(pack_peers(), indent=2))


def unpack_peers(data):
    if not hasattr(settings, 'peers'):
        settings.peers = {}
    peers_from_file = json.loads(data)
    for fingerprint_b58 in peers_from_file:
        fingerprint = pycrypto.B58().unpack(fingerprint_b58)
        settings.peers[fingerprint] = peers_from_file[fingerprint_b58]


def pack_peers():
    peers_for_file = {}
    for fingerprint in settings.peers:
        fingerprint_b58 = pycrypto.B58().pack(fingerprint)
        peers_for_file[fingerprint_b58] = settings.peers[fingerprint]
    return peers_for_file