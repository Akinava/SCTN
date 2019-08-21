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
    pass

def rm_hosts():
    if os.path.isfile(settings.hosts_file):
        os.remove(settings.hosts_file)


def save_host(ip, port, fingerprint, signal_server=False):
    settings.hosts.update(
            {pycrypto.B58().pack(fingerprint):
                {'ip': ip, 'port': port, 'signal': signal_server}})
    settings.save_hosts()


def stop_thread(server_thread):
    server_thread._tstate_lock = None
    server_thread._stop()


if __name__ == "__main__":
    print('start test')
    # rm hosts file
    rm_hosts()
    # run SS0
    signal_server_0 = host.UDPHost(handler=sstn.SignalServerHandler, host='', port=10002)

    # save hash to hosts
    save_host(
        socket.gethostbyname(socket.gethostname()),
        signal_server_0.get_port(),
        signal_server_0.get_fingerprint(),
        True)

    # run NP0
    peer_0 = host.UDPHost(handler=Handler, host='', port=10003)
    peer_0.rize_client()

    # check connect
    # run NP1
    # connect NP1 to SS0
    # run SS1
    try:
        while True:
            time.sleep(5)
    except KeyboardInterrupt:
        signal_server_0.stop()
        peer_0.stop()

    print('end test')
