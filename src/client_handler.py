# -*- coding: utf-8 -*-
__author__ = 'Akinava'
__author_email__ = 'akinava@gmail.com'
__copyright__ = 'Copyright © 2019'
__license__ = 'MIT License'
__version__ = [0, 0]

import time
from handler import Handler
from connection import Connection
from datagram import Datagram
import settings
from settings import logger
from peers import Peers
from utilit import JObj


class ClientHandler(Handler):
    def hpn_neighbour_client_request(self, request):
        response = Datagram(request.connection)
        self.send(request=request, response=response)

    def hpn_servers_request(self, request):
        # TODO first strategy / move to funk
        attempt_connect = 0
        receiving_connection = None
        last_send_time = time.time()
        while attempt_connect < settings.attempt_connect:
            if self.__is_it_time_to_connect_with_neighbour(last_send_time, receiving_connection):
                receiving_connection = self.__make_neighbour_connection_from_hpn_server_response(request)
                self.__send_hpn_servers_request(request, receiving_connection)
                attempt_connect += 1
                last_send_time = time.time()
            if self.__message_is_delivered(receiving_connection):
                logger.debug('message hpn_servers_request was delivered')
                return
            time.sleep(0.1)
        logger.warn('message hpn_servers_request was lost')
        # TODO next strategy

    def __send_hpn_servers_request(self, request, receiving_connection):
        response = Datagram(receiving_connection)
        self.send(request=request, response=response)

    def __is_it_time_to_connect_with_neighbour(self, last_send_time, receiving_connection):
        if receiving_connection is None:
            return True
        if receiving_connection.message_was_never_sent():
            return True
        return last_send_time + settings.peer_ping_time_seconds < time.time()

    def __message_is_delivered(self, receiving_connection):
        return receiving_connection.message_was_never_received() is False

    def __make_neighbour_connection_from_hpn_server_response(self, request):
        neighbour_addr = request.unpack_message.neighbour_addr
        receiving_connection = self.net_pool.create_connection(
            remote_addr=neighbour_addr._property,
            transport=self.transport,
        )
        receiving_connection.set_pub_key(request.unpack_message.neighbour_pub_key)
        receiving_connection.set_encrypt_marker(settings.request_encrypted_protocol)
        receiving_connection.type = 'client'
        return receiving_connection

    def hpn_servers_list(self, request):
        response = Datagram(request.connection)
        self.send(request=request, response=response)

    def get_hpn_servers_list(self, **kwargs):
        parser = self.parser()
        hpn_servers_list_max_length = parser.protocol.lists.hpn_servers_list.length.max
        servers_data = Peers().get_servers_list(hpn_servers_list_max_length)
        message = parser.pack_self_defined_int(len(servers_data))
        for server_data in servers_data:
            message += self.pack_server(JObj(server_data))
        return message

    def pack_server(self, server_data):
        server_data_structure = self.parser().protocol.lists.hpn_servers_list.structure
        return self.make_message_by_structure(
            structure=server_data_structure,
            server_data=server_data)

    def get_hpn_servers_pub_key(self, **kwargs):
        return kwargs['server_data'].pub_key

    def get_hpn_servers_protocol(self, **kwargs):
        return self.parser().pack_mapping(
            mapping_name='hpn_servers_protocol',
            mapping_data=kwargs['server_data'].protocol
        )

    def get_hpn_servers_addr(self, **kwargs):
        host = kwargs['server_data'].host
        port = kwargs['server_data'].port
        return self.parser().pack_addr((host, port))

    def _get_marker_encrypted_request_marker(self, **kwargs):
        return settings.request_encrypted_protocol is True

    def _get_marker_package_id_marker(self, **kwargs):
        return kwargs['response'].package_protocol.package_id_marker

    def get_requester_pub_key(self, **kwargs):
        return self.crypt_tools.get_pub_key()

    def save_hpn_servers_list(self, request):
        hpn_servers_list = request.unpack_message.hpn_servers_list._property
        Peers().save_servers_list(hpn_servers_list)
