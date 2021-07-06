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
                'verify_test_peer_hello_package_len',
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
        self.do_test_peer_hello()

    def verify_test_peer_hello_package_len(self, **kwargs):
        request_length = len(self.connection.get_request())
        required_length = self.parser.calc_structure_length()
        return required_length == request_length

    def verify_package_id_marker(self, **kwargs):
        package_protocol = kwargs['package_protocol']
        request_id_marker = self.parser.get_part('package_id_marker')
        required_id_marker = package_protocol['package_id_marker']
        return request_id_marker == required_id_marker

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
