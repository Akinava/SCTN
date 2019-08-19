#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import os
import sys
import threading
import random
import time
import socket
import json


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
    server = host.UDPHost(host='', port=port, handler=handler)
    server_tread = threading.Thread(target = server.rize_server)
    server_tread.start()
    return server


def save_host(ip, port, fingerprint, signal_server=False):
    hosts_file_json = 'src/hosts.json'
    hosts_info = {}
    if os.path.isfile(hosts_file_json):
        with open(hosts_file_json, 'r') as hosts_file:
            try:
                hosts_info = json.loads(hosts_file.read())
            except json.decoder.JSONDecodeError:
                pass
    with open(hosts_file_json, 'w') as hosts_file:
        hosts_info.update(
            {pycrypto.B58().pack(fingerprint):
                {'ip': ip, 'port': port, 'signal': signal_server}})
        hosts_file.write(json.dumps(hosts_info, indent=2))


if __name__ == "__main__":
    print('start test')
    # run SS0
    signal_server_0_port = 10002
    signal_server_0 = rize_server(signal_server_0_port, sstn.SignalServerHandler)
    fingerprint_signal_server_0 = signal_server_0.get_fingerprint()

    # save hash to hosts
    save_host(socket.gethostbyname(socket.gethostname()), signal_server_0_port, fingerprint_signal_server_0, True)

    # run NP0
    # check connect
    # run NP1
    # connect NP1 to SS0
    # run SS1
    try:
        while True:
            time.sleep(10)
    except KeyboardInterrupt:
        print('end test')
    # app is main app logic / react on event add tasks to server /
