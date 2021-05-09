# -*- coding: utf-8 -*-
__author__ = 'Akinava'
__author_email__ = 'akinava@gmail.com'
__copyright__ = "Copyright © 2019"
__license__ = "MIT License"
__version__ = [0, 0]


import sys
import os
from pathlib import Path
from datetime import datetime
import asyncio
path = Path(os.path.dirname(os.path.realpath(__file__))).parent
sys.path.append(os.path.join(path, 'src'))
import client
from settings import logger


class TestPeerHandler():
    msg_test_peer_hello = 'test peer hello'

    protocol = {
        'request': 'response',
        'test_peer_hello': 'test_peer_time',
        'test_peer_time': None,
    }

    def init(self):
        logger.info('')
        self.do_test_peer_hello()

    def define_test_peer_hello(self, connection):
        logger.info('')
        if connection.get_request() == msg_test_peer_hello:
            return True

    def do_test_peer_hello(self):
        connection = self.net_pool.get_random_client_connection()
        connection.send(msg_test_peer_hello)

    def define_test_peer_time(self, connection):
        logger.info('')


    def do_test_peer_time(self, connection):
        logger.info('')
        return datetime.now().strftime("%Y.%m.%d-%H:%M:%S")


if __name__ == '__main__':
    logger.info('test client start')
    test_client = client.Client(handler=TestPeerHandler)
    asyncio.run(test_client.run())
    logger.info('test client shutdown')
