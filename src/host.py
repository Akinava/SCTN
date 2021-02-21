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
        self.handler = handler
        self.listeners = {}
        self.connections = {}

    def connect(self, host, port):
        logger.info('host connect to {} {}'.format(host, port))

    async def create_listener(self, port):
        if self.check_port_busy(port):
            return
        logger.info('UDPHost create_listener')
        loop = asyncio.get_running_loop()
        logger.info('host create_listener on port {}'.format(port))
        transport, protocol = await loop.create_datagram_endpoint(
            lambda: self.handler(),
            local_addr=('0.0.0.0', port))
        self.listeners[port] = {
            'transport': transport,
            'protocol': protocol,
        }

    def check_port_busy(self, port):
        return port in self.listeners

    async def serve_forever(self):
        logger.info('UDPHost serve_forever')
        while self.listeners or self.connections:
            await asyncio.sleep(settings.time_check_host_is_alive)

    def shutdown_listener(self, port):
        if not port in self.listeners:
            return
        self.listeners[port]['transport'].close()
        del self.listeners[port]

    def __del__(self):
        logger.info('UDPHost __del__')
        #for port in self.listeners:
        #    self.shutdown_listener(port)
