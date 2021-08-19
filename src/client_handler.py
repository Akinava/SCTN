# -*- coding: utf-8 -*-
__author__ = 'Akinava'
__author_email__ = 'akinava@gmail.com'
__copyright__ = 'Copyright © 2019'
__license__ = 'MIT License'
__version__ = [0, 0]


from handler import Handler
from connection import Connection
import settings
from peers import Peers


class ClientHandler(Handler):
    def hpn_neighbour_client_request(self):
        return self.make_message(package_name='hpn_neighbour_client_request')

    def hpn_servers_request(self):
        package = self.parser.unpack_package()
        receiving_connection = Connection(
            transport=self.transport,
            remote_addr=package['neighbour_addr'])
        receiving_connection.set_pub_key(package['neighbour_pub_key'])
        receiving_connection.set_encrypt_marker(settings.request_encrypted_protocol)
        receiving_connection.type = 'client'

        message = self.make_message(
            package_name='hpn_servers_request',
            receiving_connection=receiving_connection)

        self.send(
            receiving_connection=receiving_connection,
            message=message,
            package_protocol_name='hpn_servers_request'
        )

    def hpn_servers_list(self):
        message = self.make_message(package_name='hpn_servers_list')
        self.send(
            message=message,
            package_protocol_name='hpn_servers_request'
        )

    def get_hpn_servers_list(self, **kwargs):
        servers_data = Peers().get_servers_list()
        hpn_servers_list_max_length = self.protocol['lists']['hpn_servers_list']['length']['max']
        servers_data = servers_data[: hpn_servers_list_max_length]
        message = self.parser.pack_self_defined_int(len(servers_data))
        for server_data in servers_data:
            message += self.pack_server(server_data)
        self.send(
            message=message,
            package_protocol_name='hpn_servers_request'
        )

    def pack_server(self, server_data):
        structure = self.protocol['lists']['hpn_servers_list']['structure']
        return self.make_message(structure=structure, server_data=server_data)

    def get_hpn_servers_pub_key(self, **kwargs):
        return kwargs['server_data']['pub_key']

    def get_hpn_servers_protocol(self, **kwargs):
        return self.parser.pack_mapping(
            mapping_name='hpn_servers_protocol',
            mapping_data=kwargs['server_data']['protocol']
        )

    def get_hpn_servers_addr(self, **kwargs):
        host = kwargs['server_data']['host']
        port = kwargs['server_data']['port']
        return self.parser.pack_addr((host, port))

    def _get_marker_encrypted_request_marker(self, **kwargs):
        return settings.request_encrypted_protocol is True

    def _get_marker_package_id_marker(self, **kwargs):
        return self.protocol['packages'][kwargs['package_name']]['package_id_marker']

    def get_requester_pub_key(self, **kwargs):
        return self.crypt_tools.get_pub_key()
