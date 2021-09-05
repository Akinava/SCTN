# -*- coding: utf-8 -*-
__author__ = 'Akinava'
__author_email__ = 'akinava@gmail.com'
__copyright__ = 'Copyright © 2019'
__license__ = 'MIT License'
__version__ = [0, 0]

import time
from handler import Handler
from connection import Connection
import settings
from settings import logger
from peers import Peers


class ClientHandler(Handler):
    def hpn_neighbour_client_request(self, connection):
        message = self.make_message(
            package_protocol_name='hpn_neighbour_client_request',
            receiving_connection=connection)

        self.send(
            package_protocol_name='hpn_neighbour_client_request',
            receiving_connection=connection,
            message=message)

    def hpn_servers_request(self, connection):
        receiving_connection = Connection(
            transport=self.transport,
            remote_addr=connection.get_unpack_request_part('neighbour_addr'))
        receiving_connection.set_pub_key(connection.get_unpack_request_part('neighbour_pub_key'))
        receiving_connection.set_encrypt_marker(settings.request_encrypted_protocol)
        receiving_connection.type = 'client'

        message = self.make_message(
            package_protocol_name='hpn_servers_request',
            receiving_connection=receiving_connection)

        self.__thread_handle_message_loss(
            message=message,
            receiving_connection=receiving_connection)

        self.send(
            message=message,
            receiving_connection=receiving_connection,
            package_protocol_name='hpn_servers_request')

    def __thread_handle_message_loss(self, **kwargs):
        self.run_stream(
            target=self.handle_message_loss,
            **kwargs)

    def handle_message_loss(self, receiving_connection, message):
        time_message_send = time.time()
        attempt_connect = settings.attempt_connect
        while attempt_connect and (
                receiving_connection.get_time_received_message() is None or \
                time_message_send > receiving_connection.get_time_received_message()):
            time.sleep(0.1)
            receiving_connection = self.net_pool.get_connection(receiving_connection)
            if time_message_send + settings.peer_ping_time_seconds > time.time():
                receiving_connection
                continue
            attempt_connect -= 1
            time_message_send = time.time()
            logger.warn('message hpn_servers_request was lost')
            self.send(
                receiving_connection=receiving_connection,
                message=message,
                package_protocol_name='hpn_servers_request')
        logger.debug('message hpn_servers_request was delivered')

    def hpn_servers_list(self, connection):
        message = self.make_message(
            receiving_connection=connection,
            package_protocol_name='hpn_servers_list')
        self.send(
            receiving_connection=connection,
            message=message,
            package_protocol_name='hpn_servers_request')

    def get_hpn_servers_list(self, **kwargs):
        servers_data = Peers().get_servers_list()
        hpn_servers_list_max_length = self.protocol['lists']['hpn_servers_list']['length']['max']
        servers_data = servers_data[: hpn_servers_list_max_length]
        message = self.parser().pack_self_defined_int(len(servers_data))
        for server_data in servers_data:
            message += self.pack_server(server_data)
        return message

    def pack_server(self, server_data):
        server_data_structure = self.protocol['lists']['hpn_servers_list']['structure']
        return self.make_message(
            package_structure=server_data_structure,
            server_data=server_data)

    def get_hpn_servers_pub_key(self, **kwargs):
        return kwargs['server_data']['pub_key']

    def get_hpn_servers_protocol(self, **kwargs):
        return self.parser().pack_mapping(
            mapping_name='hpn_servers_protocol',
            mapping_data=kwargs['server_data']['protocol']
        )

    def get_hpn_servers_addr(self, **kwargs):
        host = kwargs['server_data']['host']
        port = kwargs['server_data']['port']
        return self.parser().pack_addr((host, port))

    def _get_marker_encrypted_request_marker(self, **kwargs):
        return settings.request_encrypted_protocol is True

    def _get_marker_package_id_marker(self, **kwargs):
        return self.protocol['packages'][kwargs['package_protocol_name']]['package_id_marker']

    def get_requester_pub_key(self, **kwargs):
        return self.crypt_tools.get_pub_key()

    def save_hpn_servers_list(self, connection):
        hpn_servers_list = connection.get_unpack_request_part('hpn_servers_list')
        Peers().save_servers_list(hpn_servers_list)
