# -*- coding: utf-8 -*-
__author__ = 'Akinava'
__author_email__ = 'akinava@gmail.com'
__copyright__ = 'Copyright © 2019'
__license__ = 'MIT License'
__version__ = [0, 0]


import sys
from settings import logger
from crypt_tools import Tools as CryptTools
from connection import Connection, NetPool
from utilit import encode


class Handler:
    msg_ping = b''

    def __init__(self, message=None):
        logger.info('')
        self.net_pool = NetPool()
        self.crypt_tools = CryptTools()
        self.response = message
        self.transport = None

    def connection_made(self, transport):
        logger.info('')
        self.transport = transport

    def datagram_received(self, request, remote_addr):
        logger.info('request %s from %s' % (request, remote_addr))
        connection = Connection()
        connection.datagram_received(request, remote_addr, self.transport)
        self.net_pool.save_connection(connection)
        self.__handle(connection)

    def connection_lost(self, remote_addr):
        connection = Connection()
        connection.set_remote_addr(remote_addr)
        self.net_pool.disconnect(connection)

    def make_connection(self, remote_host, remote_port):
        connection = Connection(transport=self.transport, remote_host=remote_host, remote_port=remote_port)
        self.net_pool.save_connection(connection)
        return connection

    def __handle(self, connection):
        logger.info('')
        # TODO make a tread
        request_name = self.__define_request(connection)
        logger.info('function defined as {}'.format(request_name))
        if request_name is None:
            return
        response_function = self.__get_response_function(request_name)
        if response_function is None:
            return
        request = response_function(connection)
        if request:
            self.__send_request(connection, request)

    def __send_request(self, connection, request):
        request = encode(request)
        connection.send(request)

    def __define_request(self, connection):
        logger.info('')
        self_functions = dir(self)
        for function_name in self_functions:
            if function_name == sys._getframe().f_code.co_name:
                continue
            if not function_name.startswith('define_'):
                continue
            define_function = getattr(self, function_name)
            if not define_function(connection) is True:
                continue
            request_name = function_name.replace('define_', '')
            return request_name
        logger.warn('UDPProtocol can not define request')

    def __get_response_function(self, request_name):
        response_name = self.protocol[request_name]
        logger.info('UDPProtocol response_name {}'.format(response_name))
        response_function_name = 'do_{}'.format(response_name)
        logger.info('UDPProtocol response_function_name {}'.format(response_function_name))
        if not hasattr(self, response_function_name):
            return
        return getattr(self, response_function_name)

    def define_swarm_ping(self, connection):
        if connection.get_request() == msg_ping:
            return True
        return False

    def do_swarm_ping(self, connection):
        return msg_ping
