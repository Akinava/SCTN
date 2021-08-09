# -*- coding: utf-8 -*-
__author__ = 'Akinava'
__author_email__ = 'akinava@gmail.com'
__copyright__ = 'Copyright © 2019'
__license__ = 'MIT License'
__version__ = [0, 0]


from handler import Handler
from connection import Connection
import settings


class ClientHandler(Handler):
    def hpn_neighbour_client_request(self, **kwargs):
        return self.make_message(
            package_name='hpn_neighbour_client_request',
            receiver_connection=kwargs['receiver_connection'])

    def hpn_servers_request(self, **kwargs):
        package = self.parser.unpack_package()
        receiver_connection = Connection(
            transport=self.transport,
            remote_addr=package['neighbour_addr'])
        receiver_connection.set_pub_key(package['neighbour_pub_key'])
        receiver_connection.set_encrypt_marker(settings.request_encrypted_protocol)
        receiver_connection.type = 'client'

        message = self.make_message(
            package_name='hpn_servers_request',
            receiver_connection=receiver_connection)

        self.parser.debug_unpack_package(data=message, package_protocol_name='hpn_servers_request')

        self.send(
            connection=receiver_connection,
            message=message,
            package_protocol_name='hpn_servers_request'
        )

    def _get_marker_encrypted_request_marker(self, **kwargs):
        return settings.request_encrypted_protocol is True

    def _get_marker_package_id_marker(self, **kwargs):
        return self.protocol['packages'][kwargs['package_name']]['package_id_marker']

    def get_requester_pub_key(self, **kwargs):
        return self.crypt_tools.get_pub_key()
