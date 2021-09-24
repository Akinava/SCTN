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
from datagram import Datagram
from utilit import JObj
from settings import logger
from utilit import now
from crypt_tools import Tools as CryptTools


PROTOCOL = {
    'protocol_version': __version__,
    'packages': [
        {
            'name': 'test_peer_hello',
            'package_id_marker': 0x80,
            'define': [
                'verify_package_length',
                'verify_protocol_version',
                'verify_package_id_marker',
                'verify_receiver_fingerprint',
            ],
            'response': 'test_peer_time',
            'structure': [
                {'name': ('major_protocol_version_marker', 'minor_protocol_version_marker'), 'length': 1, 'type': 'markers'},
                {'name': 'package_id_marker', 'length': 1,  'type': 'int'},
                {'name': 'receiver_fingerprint', 'length': CryptTools.fingerprint_length}]
        },
        {
            'name': 'test_peer_time',
            'package_id_marker': 0x81,
            'define': [
                'verify_package_length',
                'verify_protocol_version',
                'verify_package_id_marker',
                'verify_receiver_fingerprint',
            ],
            'response': 'show_peer_time',
            'structure': [
                {'name': ('major_protocol_version_marker', 'minor_protocol_version_marker'), 'length': 1, 'type': 'markers'},
                {'name': 'package_id_marker', 'length': 1,  'type': 'int'},
                {'name': 'receiver_fingerprint', 'length': CryptTools.fingerprint_length},
                {'name': 'peer_time', 'length': len(now()), 'type': 'str'}]
        }
    ],
    'markers': [
        {'name': 'major_protocol_version_marker', 'start_bit': 0, 'length': 4, 'type': 'int_marker'},
        {'name': 'minor_protocol_version_marker', 'start_bit': 4, 'length': 4, 'type': 'int_marker'},
    ],
}


class Handler:
    def init(self):
        logger.info('')
        # this method is called after making the swarm see in config file parameter peer_connections

        for connection in self.net_pool.get_all_client_connections():
        # we can use same connection mark about received
            request = Datagram(connection=connection)
            request.set_package_protocol(JObj({'response': 'test_peer_hello'}))
            self.test_peer_hello(request)

            # also can we can got test_peer_hello in the past, now we need response on it with test_peer_time
            if hasattr(connection, 'swarm_status'):
                request.set_package_protocol(JObj({'response': 'test_peer_time'}))
                self.test_peer_time(request)

    def test_peer_hello(self, request):
        logger.info('')
        if self.net_pool.swarm_status != 'done':
            request.connection.swarm_status = 'done'
            return
        response = Datagram(connection=request.connection)
        self.send(request=request, response=response)

    def test_peer_time(self, request):
        response = Datagram(connection=request.connection)
        self.send(request=request, response=response)

    def get_major_protocol_version_marker(self, **kwargs):
        return self.parser().protocol.protocol_version[0]

    def get_minor_protocol_version_marker(self, **kwargs):
        return self.parser().protocol.protocol_version[1]

    def get_peer_time(self, **kwargs):
        return now()

    def verify_protocol_version(self, parser):
        if parser.unpack_package.major_protocol_version_marker > parser.protocol.protocol_version[0]:
            return False
        if parser.unpack_package.minor_protocol_version_marker > parser.protocol.protocol_version[1]:
            return False
        return True


if __name__ == '__main__':
    logger.info('test client start')
    test_client = Client(handler=Handler, protocol=PROTOCOL)
    try:
        asyncio.run(test_client.run())
    except KeyboardInterrupt:
        logger.info('test client interrupted')
    logger.info('test client shutdown')
