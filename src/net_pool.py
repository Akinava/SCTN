# -*- coding: utf-8 -*-
__author__ = 'Akinava'
__author_email__ = 'akinava@gmail.com'
__copyright__ = 'Copyright © 2019'
__license__ = 'MIT License'
__version__ = [0, 0]


from utilit import Singleton
from settings import logger
import settings


class NetPool(Singleton):
    def __init__(self):
        logger.info('NetPool')
        self.__group = []

    def __clean_groups(self):
        alive_group_tmp = []
        for connection in self.__group:
            if connection.last_received_message_is_over_time_out() is True:
                logger.debug('host {} disconnected bt timeout'.format(connection))
                continue
            self.__mark_connection_type(connection)
            alive_group_tmp.append(connection)
        self.__group = alive_group_tmp

    def has_enough_connections(self):
        logger.info('NetPool')
        return len(self.get_all_client_connections()) >= settings.peer_connections

    def __mark_connection_type(self, connection):
        if not hasattr(connection, 'type'):
            connection.set_type('client')

    def save_connection(self, connection):
        logger.info('NetPool')
        if connection in self.__group:
            self.__update_connection_in_group(connection)
        else:
            self.__put_connection_in_group(connection)
        return connection

    def __update_connection_in_group(self, new_connection):
        connection_index = self.__group.index(new_connection)
        old_connection = self.__group[connection_index]
        self.__copy_connection_property(new_connection, old_connection)
        self.__group[connection_index] = new_connection

    def __copy_connection_property(self, new_connection, old_connection):
        new_connection.set_pub_key(old_connection.get_pub_key())

    def __put_connection_in_group(self, connection):
        self.__group.append(connection)

    def get_all_connections(self):
        self.__clean_groups()
        return self.__group

    def get_all_client_connections(self):
        logger.info('')
        return self.__filter_connection_by_type('client')

    def get_random_client_connection(self):
        group = self.__filter_connection_by_type('client')
        return random.choice(group) if group else None

    def get_server_connections(self):
        logger.info('NetPool')
        return self.__filter_connection_by_type('server')

    def has_client_connection(self):
        group = self.__filter_connection_by_type('client')
        return len(group) > 0

    def __filter_connection_by_type(self, my_type):
        logger.info('NetPool {}'.format(my_type))
        self.__clean_groups()
        group = []
        for connection in self.__group:
            if not hasattr(connection, 'type'):
                continue
            if connection.get_type() == my_type:
                group.append(connection)
        return group

    def shutdown(self):
        for connection in self.__group:
            connection.shutdown()
        self.__group = []
