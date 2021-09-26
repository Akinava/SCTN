# -*- coding: utf-8 -*-
__author__ = 'Akinava'
__author_email__ = 'akinava@gmail.com'
__copyright__ = 'Copyright © 2019'
__license__ = 'MIT License'
__version__ = [0, 0]

import time
from handler import Handler
from datagram import Datagram
import settings
from settings import logger
from peers import Peers
from utilit import JObj


class ClientHandler(Handler):
    def extended_get_pub_key(self, request):
        def copy_connection_property(connection_src, connection_dst):
            connection_dst.set_pub_key(connection_src.get_pub_key())
            connection_dst.set_encrypt_marker(connection_src.get_encrypt_marker())
            connection_dst.sent_message_time = connection_src.sent_message_time

        fingerprint = request.raw_message[: self.crypt_tools.fingerprint_length]
        connection = self.net_pool.get_connection_by_fingerprint(fingerprint)
        if connection is None:
            return None

        copy_connection_property(connection, request.connection)
        return connection.get_pub_key()

    def hpn_neighbours_client_request(self, request):
        response = Datagram(request.connection)
        self.__delivered_by_direct_send(request, response)

    def __do_hpn_servers_request(self, request, receiving_connection):
        response = Datagram(receiving_connection)
        if self.__delivered_by_direct_send(request, response):
            self.__has_enough_client_connections()
        # TODO next delivery strategy

    def __delivered_by_direct_send(self, request, response):
        def sent_message_is_over_time_out(sent_message_time):
            return sent_message_time + settings.peer_timeout_seconds < time.time()

        first_sent_message_time = time.time()
        self.net_pool.add_connection(response.connection)
        while response.connection.message_was_never_received():
            if response.connection.last_sent_message_is_over_ping_time():
                self.send(request=request, response=response)
            if sent_message_is_over_time_out(first_sent_message_time):
                logger.warn('message {} to {} is lost'.format(response.package_protocol.name, response.connection))
                self.net_pool.disconnect(response.connection)
                return False
            time.sleep(0.1)
        logger.debug('message {} to {} is delivered'.format(response.package_protocol.name, response.connection))
        return True

    def hpn_servers_request(self, request):
        self.__handle_disconnect_flag(request)
        neighbours_connections = self.__get_neighbours_connections_from_hpn_server_response(request)
        for receiving_connection in neighbours_connections:
            self.run_stream(target=self.__do_hpn_servers_request, request=request, receiving_connection=receiving_connection)

    def __handle_disconnect_flag(self, request):
        if request.unpack_message.disconnect_flag:
            self.net_pool.disconnect(request.connection)

    def __get_neighbours_connections_from_hpn_server_response(self, request):
        neighbours_data_list = request.unpack_message.hpn_clients_list
        neighbours_connections = []
        for neighbour_data in neighbours_data_list:
            neighbours_connections.append(self.__get_neighbour_connection(neighbour_data))
        return neighbours_connections

    def __get_neighbour_connection(self, neighbour_data):
        neighbour_connection = self.net_pool.create_connection(
            remote_addr=neighbour_data.hpn_clients_addr._property,
            transport=self.transport,
        )
        neighbour_connection.set_pub_key(neighbour_data.hpn_clients_pub_key)
        neighbour_connection.set_encrypt_marker(settings.request_encrypted_protocol)
        neighbour_connection.type = 'client'
        return neighbour_connection

    def hpn_servers_list(self, request):
        response = Datagram(request.connection)
        self.send(request=request, response=response)

    def get_hpn_servers_list(self, **kwargs):
        hpn_servers_list = []
        parser = self.parser()
        hpn_servers_list_max_length = parser.protocol.lists.hpn_servers_list.length.max
        servers_data = Peers().get_servers_list(hpn_servers_list_max_length)
        for server_data in servers_data:
            hpn_servers_list.append(self.pack_server(JObj(server_data)))
        return hpn_servers_list

    def pack_server(self, server_data):
        server_data_structure = self.parser().protocol.lists.hpn_servers_list.structure
        return self.make_message_by_structure(
            structure=server_data_structure,
            server_data=server_data)

    def get_hpn_servers_pub_key(self, **kwargs):
        return kwargs['server_data'].pub_key

    def get_hpn_servers_protocol(self, **kwargs):
        return kwargs['server_data'].protocol

    def get_hpn_servers_addr(self, **kwargs):
        return kwargs['server_data'].host, kwargs['server_data'].port

    def get_encrypted_request_marker(self, **kwargs):
        return 1 if settings.request_encrypted_protocol else 0

    def get_requester_pub_key(self, **kwargs):
        return self.crypt_tools.get_pub_key()

    def save_hpn_servers_list(self, request):
        hpn_servers_list = request.unpack_message.hpn_servers_list._property
        Peers().save_servers_list(hpn_servers_list)

    def __has_enough_client_connections(self):
        if self.net_pool.swarm_status != 'in progress':
            return
        if not self.net_pool.has_enough_client_connections():
            return
        self.net_pool.swarm_status = 'done'
        if not hasattr(self, 'init'):
            return
        self.init()
