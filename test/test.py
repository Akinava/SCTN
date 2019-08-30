#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import os
import sys
import time


__author__ = 'Akinava'
__author_email__ = 'akinava@gmail.com'
__copyright__ = "Copyright © 2019"
__license__ = "MIT License"
__version__ = [0, 0]


test_dir = os.path.dirname(os.path.abspath(__file__))
src_dir = os.path.join(test_dir, '../src')
sys.path.append(src_dir)
import host
import sstn
import settings


class Handler:
    def __init__(self, interface):
        self.__sctn = sstn.SignalClientHandler(interface, self)

    def handle_request(self, msg, connection):
        print ('### Handler.handle_request')
        # do something
        print ('swarm peer {} message {} bytes from connection {}'.format(self, len(msg), connection))

    def send(self, msg, connection):
        print ('Handler.send')
        self.__interface.send(msg, connection)

    def close(self):
        self.__sctn.close()


def rm_peers():
    if os.path.isfile(settings.peers_file):
        os.remove(settings.peers_file)


def stop_thread(server_thread):
    server_thread._tstate_lock = None
    server_thread._stop()


if __name__ == "__main__":
    print('start test')
    # rm peers file
    rm_peers()

    # run SS0
    peers = []

    signal_server_0 = host.UDPHost(handler=sstn.SignalServerHandler, host='', port=10002)
    peers.append(signal_server_0)
    # save fingerprint to peers
    if not os.path.isfile(settings.peers_file):
        settings.add_peer(
            {'ip': '127.0.0.1',
             'port': 10002,
             'fingerprint': signal_server_0.get_fingerprint(),
             'signal': True})

    # run NP
    for port in range(10003, 10004):
        peers.append(host.UDPHost(handler=Handler, host='', port=port))

    try:
        while True:
            time.sleep(5)
    except KeyboardInterrupt:
        for h in peers:
            h.stop()

    print('end test')
