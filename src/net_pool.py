# -*- coding: utf-8 -*-
__author__ = 'Akinava'
__author_email__ = 'akinava@gmail.com'
__copyright__ = 'Copyright © 2019'
__license__ = 'MIT License'
__version__ = [0, 0]


import random
from utilit import Singleton
from settings import logger
import settings


class NetPool(Singleton):
    def __init__(self):
        #logger.debug('NetPool')
        self.__group = []

    def __clean_groups(self):
        alive_group_tmp = []
        for connection in self.__group:
            if connection.last_received_message_is_over_time_out() is True:
                logger.debug('host {} disconnected by timeout'.format(connection))
                continue
            alive_group_tmp.append(connection)
        self.__group = alive_group_tmp

    def has_enough_connections(self):
        #logger.debug('')
        return len(self.get_all_client_connections()) >= settings.peer_connections

    def save_connection(self, connection):
        #logger.debug('')
        if connection in self.__group:
            self.__update_connection_in_group(connection)
        else:
            self.__put_connection_in_group(connection)

    def get_connection(self, connection):
        return self.__group[self.__group.index(connection)]

    def __update_connection_in_group(self, new_connection):
        connection_index = self.__group.index(new_connection)
        old_connection = self.__group[connection_index]
        self.copy_connection_property(new_connection, old_connection)
        self.__group[connection_index] = new_connection

    def copy_connection_property(self, new_connection, old_connection):
        new_connection.set_pub_key(old_connection.get_pub_key())
        new_connection.set_encrypt_marker(old_connection.get_encrypt_marker())
        new_connection.set_time_sent_message(old_connection.get_time_sent_message())
        new_connection.type = old_connection.type

    def __put_connection_in_group(self, connection):
        self.__group.append(connection)

    def get_all_connections(self):
        self.__clean_groups()
        return self.__group

    def get_all_client_connections(self):
        #logger.debug('')
        return self.__filter_connection_by_type('client')

    def get_random_client_connection(self):
        group = self.__filter_connection_by_type('client')
        return random.choice(group) if group else None

    def get_server_connections(self):
        logger.debug('')
        return self.__filter_connection_by_type('server')

    def has_client_connection(self):
        group = self.__filter_connection_by_type('client')
        return len(group) > 0

    def __filter_connection_by_type(self, my_type):
        self.__clean_groups()
        group = []
        for connection in self.__group:
            if connection.type == my_type:
                group.append(connection)
        return group

    def find_connection_by_fingerprint(self, fingerprint):
        for connection in self.__group:
            if connection.get_fingerprint() == fingerprint:
                return connection
        return None

    def shutdown(self):
        for connection in self.__group:
            connection.shutdown()
        self.__group = []
