# -*- coding: utf-8 -*-
__author__ = 'Akinava'
__author_email__ = 'akinava@gmail.com'
__copyright__ = "Copyright © 2019"
__license__ = "MIT License"
__version__ = [0, 0]


import asyncio
from settings import logger


class UDPHost:
    def __init__(self, handler):
        logger.info('host init')
        self.handler = handler
        self.listeners = {}
        self.connections = {}

    def connect(self, host, port):
        logger.info('host connect to {} {}'.format(host, port))

    async def create_listener(self, port):
        self.set_loop()
        logger.info('host create_listener on port {}'.format(port))
        transport, protocol = await self.loop.create_datagram_endpoint(
            lambda: self.handler(),
            local_addr=('0.0.0.0', port))
        self.listeners[port] = {
            'transport': transport,
            'protocol': protocol,
        }

    def set_loop(self):
        if not hasattr(self, 'loop'):
            self.loop = asyncio.get_running_loop()

    def shutdown_listener(self, port):
        if not port in self.listeners:
            return
        self.listeners[port]['transport'].close()
        del self.listeners[port]

    def __del__(self):
        for port in self.listeners:
            self.shutdown_listener(port)
