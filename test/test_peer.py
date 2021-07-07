# -*- coding: utf-8 -*-
__author__ = 'Akinava'
__author_email__ = 'akinava@gmail.com'
__copyright__ = "Copyright © 2019"
__license__ = "MIT License"
__version__ = [0, 0]


import sys
import os
from pathlib import Path
import asyncio
path = Path(os.path.dirname(os.path.realpath(__file__))).parent
sys.path.append(os.path.join(path, 'src'))


from client_host import Client
from settings import logger
from utilit import now


PROTOCOL = {
    'protocol_version': __version__,
    'packages': {
        'test_peer_hello': {
            'name': 'test_peer_hello',
            'package_id_marker': 128,
            'define': [
                'verify_package_length',
                'verify_package_id_marker'],
            'response': 'test_peer_time',
            'structure': [
                {'name': 'package_id_marker', 'length': 1}]
        },
        'test_peer_time': {
            'name': 'test_peer_time',
            'package_id_marker': 129,
            'define': 'verify_package_id_marker',
            'structure': [
                {'name': 'package_id_marker', 'length': 1},
                {'name': 'peer_time', 'length': len(now())}]
        }
    }
}


class Handler:
    def init(self):
        logger.info('')
        # this method is called after making the swarm see in config file parameter peer_connections
        self.test_peer_hello()

    def test_peer_hello(self):
        return self.make_message(package_name='test_peer_hello')

    def test_peer_time(self):
        logger.info('')
        return self.make_message(package_name='test_peer_time')

    def get_peer_time(self, **kwarg):
        return now()


if __name__ == '__main__':
    logger.info('test client start')
    test_client = Client(handler=Handler, protocol=PROTOCOL)
    try:
        asyncio.run(test_client.run())
    except KeyboardInterrupt:
        logger.info('test client interrupted')
    logger.info('test client shutdown')
