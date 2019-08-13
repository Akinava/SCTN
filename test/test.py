#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import os
import sys


__author__ = 'Akinava'
__author_email__ = 'akinava@gmail.com'
__copyright__ = "Copyright © 2019"
__license__ = "MIT License"
__version__ = [0, 0]


test_dir = os.path.dirname(os.path.abspath(__file__))
src_dir = os.path.join(test_dir, '../src')
sys.path.append(src_dir)
import host


class Handler:
    def __init__(self, connection, data):
        self.connection = connection
        self.data = data

    def handle(self):
        client_msg = "Message from Client:{}".format(self.data.decode('utf8'))
        client_connection  = "Client IP Address:{}".format(self.connection)
        print(client_msg)
        print(client_connection)


class Main:
    pass


if __name__ == "__main__":
    # server = UDMPost()
    # app =  Main(host=server)
    #
    print('start test')
    server = host.UDPHost(host='', port=10002, handler=Handler)
    try:
        server.start()
    except KeyboardInterrupt:
        print('end test')
