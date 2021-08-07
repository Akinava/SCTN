# -*- coding: utf-8 -*-
__author__ = 'Akinava'
__author_email__ = 'akinava@gmail.com'
__copyright__ = 'Copyright © 2019'
__license__ = 'MIT License'
__version__ = [0, 0]


from handler import Handler
import settings


class ClientHandler(Handler):
    def hpn_neighbour_client_request(self, **kwargs):
        return self.make_message(
            package_name='hpn_neighbour_client_request',
            receiver_connection=kwargs['receiver_connection'])

    def hpn_servers_request(self, **kwargs):
        # message = self.make_message(
        #     package_name='hpn_servers_request',
        #     receiver_connection=kwargs['receiver_connection'])
        print('kwargs', kwargs)
        print('hpn_servers_request >>>', kwargs)

    def _get_marker_encrypted_request_marker(self, **kwargs):
        return settings.request_encrypted_protocol is True

    def _get_marker_package_id_marker(self, **kwargs):
        return self.protocol['packages'][kwargs['package_name']]['package_id_marker']

    def get_requester_open_key(self, **kwargs):
        return self.crypt_tools.get_open_key()
