# -*- coding: utf-8 -*-
__author__ = 'Akinava'
__author_email__ = 'akinava@gmail.com'
__copyright__ = 'Copyright © 2019'
__license__ = 'MIT License'
__version__ = [0, 0]


import random
from net_pool import NetPool
from settings import logger
import settings


class ClientNetPool(NetPool):
    def has_enough_client_connections(self):
        return len(self.get_all_client_connections()) >= settings.peer_connections

    def get_connection(self, connection):
        return self.__group[self.__group.index(connection)]

    def get_connection_by_fingerprint(self, fingerprint):
        for connection in self.get_all_connections():
            if connection.get_fingerprint() == fingerprint:
                return connection

    def copy_connection_property(self, src_connection, dst_connection):
        logger.info('src {}, dst {}'.format(src_connection, dst_connection))
        dst_connection.set_pub_key(src_connection.get_pub_key())
        dst_connection.set_encrypt_marker(src_connection.get_encrypt_marker())
        dst_connection.type = src_connection.type

    def __put_connection_in_group(self, connection):
        self.__group.append(connection)

    def get_all_client_connections(self):
        return self.__filter_connection_by_type('client')

    def get_random_client_connection(self):
        group = self.__filter_connection_by_type('client')
        return random.choice(group) if group else None

    def get_server_connections(self):
        return self.__filter_connection_by_type('server')

    def has_client_connection(self):
        group = self.__filter_connection_by_type('client')
        return len(group) > 0

    def __filter_connection_by_type(self, my_type):
        self.clean_connections_list()
        group = []
        for connection in self.connections_list:
            if hasattr(connection, 'type') and connection.type == my_type:
                group.append(connection)
        return group
