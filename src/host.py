# -*- coding: utf-8 -*-
__author__ = 'Akinava'
__author_email__ = 'akinava@gmail.com'
__copyright__ = 'Copyright © 2019'
__license__ = 'MIT License'
__version__ = [0, 0]


import asyncio
import settings
from settings import logger


class UDPHost:
    def __init__(self, handler):
        logger.info('UDPHost init')
        self.handler = handler()
        self.connections = {}

    def connect(self, host, port):
        logger.info('host connect to {} {}'.format(host, port))

    async def create_listener(self, port):
        logger.info('UDPHost create_listener')
        loop = asyncio.get_running_loop()
        logger.info('host create_listener on port {}'.format(port))
        transport, protocol = await loop.create_datagram_endpoint(
            lambda: self.handler,
            local_addr=('0.0.0.0', port))
        self.listener = {
            'port': port,
            'transport': transport,
            'protocol': protocol,
        }

    async def serve_forever(self):
        logger.info('UDPHost serve_forever')
        while self.listener or self.connections:
            self.ping_connections()
            self.clean_connections()
            await asyncio.sleep(settings.peer_ping_time_seconds)

    def ping_connections(self):
        for connection in self.connections:
            self.send(connection, self.handler.do_swarm_ping())

    def send(self, connection, message):
        logger.info('UDPHost send')
        # TODO

    def clean_connections(self):
        alive_connections = []
        for connection in self.connections:
            if connection.is_alive():
                alive_connections.append(connection)
        self.connections = alive_connections

    def shutdown_listener(self):
        self.listener['transport'].close()
        self.listener = {}

    def __del__(self):
        logger.info('UDPHost __del__')
        #for port in self.listeners:
        #    self.shutdown_listener()
