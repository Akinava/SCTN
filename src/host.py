# -*- coding: utf-8 -*-
__author__ = 'Akinava'
__author_email__ = 'akinava@gmail.com'
__copyright__ = 'Copyright © 2019'
__license__ = 'MIT License'
__version__ = [0, 0]


import asyncio
import settings
from settings import logger
from connection import Connection, NetPool


class Host:
    def __init__(self, handler):
        logger.info('Host init')
        self.handler = handler
        self.connections = []
        self.listener = None
        self.local_host = settings.local_host

    def connect(self, host, port):
        logger.info('host connect to {} {}'.format(host, port))

    async def create_listener(self, port):
        logger.info('Host create_listener')
        loop = asyncio.get_running_loop()
        logger.info('host create_listener on port {}'.format(port))

        transport, protocol = await loop.create_datagram_endpoint(
            lambda: self.handler(),
            local_addr=(self.local_host, port))
        self.listener = Connection()
        self.listener.set_listener(
            local_port=port,
            transport=transport,
            protocol=protocol)

    async def send(self, connection, message, local_port=None):
        logger.info('Host send')

        loop = asyncio.get_running_loop()
        on_con_lost = loop.create_future()
        local_addr = (self.local_host, local_port) if local_port else None

        transport, protocol = await loop.create_datagram_endpoint(
            lambda: self.handler(message, on_con_lost),
            remote_addr=connection.get_remote_addr(),
            local_addr=local_addr)

        connection.set_transport(transport)
        connection.set_protocol(protocol)
        connettion.set_net(self.connections)
        self.connections.append(connection)

        try:
            await on_con_lost
        finally:
            connection.close_transport()

    async def serve_forever(self):
        logger.info('Host serve_forever')
        while self.connections:
            self.ping_connections()
            await asyncio.sleep(settings.peer_ping_time_seconds)

    def ping_connections(self):
        for connection in self.connections:
            if connection.is_alive():
                self.send(connection, self.handler.do_swarm_ping())
            else:
                connection.shutdown()

    def __del__(self):
        logger.info('')
