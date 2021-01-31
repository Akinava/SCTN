# -*- coding: utf-8 -*-
__author__ = 'Akinava'
__author_email__ = 'akinava@gmail.com'
__copyright__ = "Copyright © 2019"
__license__ = "MIT License"
__version__ = [0, 0]


import sys
import asyncio
sys.path.append('../src')
import client
from settings import logger


class ClientHandler():
    protocol = {
        'request': 'response',
        'peer_hello': None,
    }

    def define_peer_hello(self, request):
        if request == 'peer hello':
            return True


if __name__ == '__main__':
    logger.info('test client start')
    test_client = client.Client(handler=ClientHandler)
    asyncio.run(test_client.run())
    logger.info('test client shutdown')
