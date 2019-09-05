# FIXME put all variable in to config.json
# parce and put variable as local
import json
import os
import pycrypto

config_file = 'src/config.json'
peers = {}


def pack_peers():
    peers_for_file = {}
    for fingerprint in peers:
        fingerprint_b58 = pycrypto.B58().pack(fingerprint)
        peers_for_file[fingerprint_b58] = peers[fingerprint]
    return peers_for_file


def unpack_peers(data):
    peers_from_file = json.loads(data)
    for fingerprint_b58 in peers_from_file:
        fingerprint = pycrypto.B58().unpack(fingerprint_b58)
        peers[fingerprint] = peers_from_file[fingerprint_b58]


def import_config():
    with open(config_file, 'r') as cfg_file:
        config = json.loads(cfg_file.read())
        for k, v in config.items():
            globals()[k] = v


def import_peers():
    if os.path.isfile(peers_file):
        with open(peers_file, 'r') as f:
            try:
                unpack_peers(f.read())
            except json.decoder.JSONDecodeError:
                pass


def add_peer(peer):
    peer_data = {peer['fingerprint']:
                 {'ip': peer['ip'],
                  'port': peer['port']}}
    if peer.get('signal'):
        peer_data[peer['fingerprint']]['signal'] = True
    peers.update(peer_data)
    save_peers()


def save_peers():
    with open(peers_file, 'w') as f:
        f.write(json.dumps(pack_peers(), indent=2))


import_config()
import_peers()
