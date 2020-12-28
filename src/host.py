# -*- coding: utf-8 -*-
__author__ = 'Akinava'
__author_email__ = 'akinava@gmail.com'
__copyright__ = "Copyright © 2019"
__license__ = "MIT License"
__version__ = [0, 0]

from settings import logger
import settings
import socket


class UDPHost:
    def __init__(self, handler, host='', port=settings.default_port):
        self.__handler = handler
        self.__host = host
        self.__port = port

    def create_listener(self):
        logger.info('host create listener on host "{}" and port {}'.format(self.__host, self.__port))
        self.sock = socket.socket(family=socket.AF_INET, type=socket.SOCK_DGRAM)
        self.sock.bind((self.__host, self.__port))

    def listener_start(self):
        self.create_listener()
        logger.info('create_listener')
        while True:
            msg, peer = self.sock.recvfrom(settings.socket_buffer_size)
            response = self.__handle(msg, peer)
            if response is None:
                continue
            self.sock.sendto(response, peer)

    def run_swarm_watcher(self):
        logger.info('run_swarm_watcher')
        # TODO
        pass
