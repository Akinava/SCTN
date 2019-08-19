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

'''
class Handler:
    def __init__(self, connection, data):
        self.connection = connection
        self.data = data

    def handle(self):
        client_msg = "Message from Client:{}".format(self.data.decode('utf8'))
        client_connection  = "Client IP Address:{}".format(self.connection)
        print(client_msg)
        print(client_connection)
'''

'''
class MainThread:
    def __init__(self, network):
        self.network = network

    def run(self):
        server = host.UDPHost(host='', port=10002, handler=self)

    def event_generator(self):
        time.sleep(random.randint(5, 10))
        event_msg = self.message_generator()
        # encrypt messages
        # put messages in queue
        # send messages

    def handle_network_event(self, connection, data):
        pass

    def message_generator(self):
        msg = 'bla'
        msg *= random.randint(1, 5)
        msg += random.choice(['.', '!', '?'])
        return msg.encode('utf8')
'''

def rize_server(port, handler):
    server = host.UDPHost(handler=handler, host='', port=port)
    server_thread = threading.Thread(target = server.rize_server)
    server_thread.start()
    return server, server_thread


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
    signal_server_0_port = 10002
    signal_server_0, ss_0_thread = rize_server(signal_server_0_port, sstn.SignalServerHandler)

    # save hash to hosts
    save_host(
        socket.gethostbyname(socket.gethostname()),
        signal_server_0_port,
        signal_server_0.get_fingerprint(),
        True)

    # run NP0
    # check connect
    # run NP1
    # connect NP1 to SS0
    # run SS1
    try:
        while True:
            time.sleep(5)
    except KeyboardInterrupt:
        stop_thread(ss_0_thread)

    print('end test')
