#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import os
import sys
import threading
import random
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


if __name__ == "__main__":
    print('start test')
    app = MainThread(network=host.UDPHost)
    try:
        app.run()
    except KeyboardInterrupt:
        print('end test')
    # app is main app logic / react on event add tasks to server /
