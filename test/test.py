#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import os
import sys
import threading
import random
import time
import socket
import json
import ctypes


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
import pycrypto
import settings


class Handler(sstn.SignalClientHandler):
    def __init__(self, interface):
        self.__ecdsa = pycrypto.ECDSA()
        # TODO reverse dependency host -> sstn -> handler
        self.__sctn = sstn.SignalClientHandler(interface, self.__ecdsa)
        self.__interface = interface

    def close(self):
        self.__sctn.close()

    def handle_request(self, msg, peer):
        if self.__handle_sctn_request(peer, msg):
            return
        print ('swarm peer {} message from peer {}'.format(self.__interface.get_port(), peer))

    def __handle_sctn_request(self, peer, msg):
        if self.__sctn.handle_request(msg, peer) is True:
            print ('swarm peer {} message from sstn {}'.format(self.__interface.get_port(), peer))
            return True
        return False


def rm_peers():
    if os.path.isfile(settings.peers_file):
        os.remove(settings.peers_file)


def save_host(ip, port, fingerprint, signal_server=False):
    settings.peers.update(
            {fingerprint:
                {'ip': ip, 'port': port, 'signal': signal_server}})
    settings.save_peers()


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
    save_host(
        '127.0.0.1',
        #'127.0.1.1',
        # check that response from sstn '127.0.1.1' should be refuse.
        #socket.gethostbyname(socket.gethostname()),
        signal_server_0.get_port(),
        signal_server_0.get_fingerprint(),
        True)

    # run NP
    for port in range(10003, 10005):
        peers.append(host.UDPHost(handler=Handler, host='', port=port))

    try:
        while True:
            time.sleep(5)
    except KeyboardInterrupt:
        for h in peers:
            h.stop()

    print('end test')
