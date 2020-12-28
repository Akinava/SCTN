# -*- coding: utf-8 -*-
__author__ = 'Akinava'
__author_email__ = 'akinava@gmail.com'
__copyright__ = "Copyright © 2019"
__license__ = "MIT License"
__version__ = [0, 0]


from settings import logger
import settings
import host
import protocol
import crypt_tools


class Client:
    def __init__(self, handler, host='', port=settings.default_port):
        self.__user_handler = handler
        self.__host = host
        self.__port = port

    def run(self):
        client_handler = protocol.Handler(protocol.client, crypt_tools=crypt_tools.Tools())
        self.__client = host.UDPHost(handler=client_handler, host=self.__host, port=self.__port)
        self.__client.run_swarm_watcher()

