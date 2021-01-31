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
import asyncio


class ServerHandler(protocol.GeneralProtocol):
    protocol = {
        'request': 'response',
        'swarm_ping': None,
        'swarm_hello': 'first_swarm_peer',
    }

    def do_first_swarm_peer(self, request):
        # TODO
        return ''


class Server(host.UDPHost):
    async def run(self):
        self.create_listener(settings.default_port)
        self.crypto = crypt_tools.Tools()


if __name__ == '__main__':
    logger.info('server start')
    server = Server(ServerHandler)
    asyncio.run(server.run())
    logger.info('server shutdown')
