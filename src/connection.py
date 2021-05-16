# -*- coding: utf-8 -*-
__author__ = 'Akinava'
__author_email__ = 'akinava@gmail.com'
__copyright__ = 'Copyright © 2019'
__license__ = 'MIT License'
__version__ = [0, 0]


import struct
from time import time
import random
from utilit import Singleton, encode
import settings
from settings import logger


class Connection:
    def __init__(self, local_host=None, local_port=None, remote_host=None, remote_port=None, transport=None):
        if local_host: self.__set_local_host(local_host)
        if local_port: self.__set_local_port(local_port)
        if remote_host: self.__set_remote_host(remote_host)
        if remote_port: self.__set_remote_port(remote_port)
        if transport: self.__set_transport(transport)
        self.__set_last_response()

    def __eq__(self, connection):
        if self.__remote_host != connection.__remote_host:
            return False
        if self.__remote_port != connection.__remote_port:
            return False
        return True

    def is_alive(self):
        if self.transport.is_closing():
            return False
        return True

    def __last_send_made_over_peer_timeout_but_has_no_request(self):
        return time() - self.__last_response > settings.peer_timeout_seconds

    def last_request_is_time_out(self):
        if not hasattr(self, '__last_request'):
            if self.__last_send_made_over_peer_timeout_but_has_no_request():
                return True
            return None
        return time() - self.__last_request > settings.peer_timeout_seconds

    def last_response_is_over_ping_time(self):
        return time() - self.__last_response > settings.peer_ping_time_seconds

    def __set_last_response(self):
        self.__last_response = time()

    def __set_last_request(self):
        self.__last_request = time()

    def __set_transport(self, transport):
        self.transport = transport

    def __set_protocol(self, protocol):
        self.__protocol = protocol

    def __set_local_host(self, local_host):
        self.local_host = local_host

    def __set_local_port(self, local_port):
        self.local_port = local_port

    def __set_remote_host(self, remote_host):
        self.__remote_host = remote_host

    def __set_remote_port(self, remote_port):
        self.__remote_port = remote_port

    def __set_request(self, request):
        self.__request = request

    def get_request(self):
        return self.__request

    def update_request(self, connection):
        self.__request = connection.get_request()
        self.__set_last_request()

    def set_fingerprint(self, fingerprint):
        self.fingerprint = fingerprint

    def get_fingerprint(self):
        return self.fingerprint

    def dump_addr(self):
        return struct.pack('>BBBBH', *(map(int, self.__remote_host.split('.'))), self.__remote_port)

    def datagram_received(self, request, remote_addr, transport):
        self.set_remote_addr(remote_addr)
        self.__set_request(request)
        self.__set_transport(transport)

    def set_remote_addr(self, addr):
        self.__set_remote_host(addr[0])
        self.__set_remote_port(addr[1])

    def send(self, response):
        logger.info('')
        self.transport.sendto(encode(response), (self.__remote_host, self.__remote_port))
        self.__set_last_response()

    def shutdown(self):
        if self.transport.is_closing():
            return
        self.transport.close()


class NetPool(Singleton):
    def __init__(self):
        self.__group = []

    def __clean_groups(self):
        alive_group_tmp = []
        for connection in self.__group:
            if connection.last_request_is_time_out() is True:
                connection.shutdown()
                continue
            self.__mark_connection_type(connection)
            alive_group_tmp.append(connection)
        self.__group = alive_group_tmp

    def __mark_connection_type(self, connection):
        if not hasattr(connection, 'type'):
            connection.type = 'client'

    def save_connection(self, new_connection):
        if not new_connection in self.__group:
            self.__group.append(new_connection)
            return
        connection_index = self.__group.index(new_connection)
        old_connection = self.__group[connection_index]
        old_connection.update_request(new_connection)

    def get_all_connections(self):
        self.__clean_groups()
        return self.__group

    def get_random_client_connection(self):
        group = self.__filter_connection_by_type('client')
        return random.choice(group) if group else None

    def get_server_connections(self):
        return self.__filter_connection_by_type('server')

    def has_client_connection(self):
        group = self.__filter_connection_by_type('client')
        return len(group) > 0

    def __filter_connection_by_type(self, my_type):
        self.__clean_groups()
        group = []
        for connection in self.__group:
            if not hasattr(connection, 'type'):
                continue
            if connection.type == my_type:
                group.add(connection)
        return group

    def shutdown(self):
        for connection in self.__group:
            connection.shutdown()
        self.__group = []
