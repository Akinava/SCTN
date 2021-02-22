# -*- coding: utf-8 -*-
__author__ = 'Akinava'
__author_email__ = 'akinava@gmail.com'
__copyright__ = 'Copyright © 2019'
__license__ = 'MIT License'
__version__ = [0, 0]


from settings import logger
import settings
import host
import protocol


class ClientHandler(protocol.GeneralProtocol):
    protocol = {
        'request': 'response',
        'swarm_ping': None,
        'swarm_hello': 'swarm_servers',
        'first_swarm_peer': None,
    }

    def define_first_swarm_peer(self, request):
        # connect to peer
        # TODO
        pass


class Client(host.UDPHost):
    def __init__(self, handler):
        logger.info('Client init')
        super(Client, self).__init__(handler=ClientHandler)
        self.extend_handler(handler)

    async def run(self):
        logger.info('Client run')
        await self.create_listener(settings.default_port)
        await self.serve_swarm()

    async def serve_swarm(self):
        while True:
            if self.are_enough_connections():
                await asyncio.sleep(settings.time_check)
                continue
            if self.ask_client_for_connections():
                continue
            if self.ask_server_for_connections():
                continue

    def ask_client_for_connections(self):
        # read clients list
        # get random
        # send request to client
        # TODO
        pass

    def ask_server_for_connections(self):
        # read servers list
        # get random
        # send request to server
        # TODO
        pass

    def are_enough_connections(self):
        return len(self.connections) >= settings.peer_connections

    def extend_handler(self, handler):
        logger.info('Client extend')
        self.handler.protocol.update(handler.protocol)
        for func_name in dir(handler):
            if hasattr(self.handler, func_name):
                continue
            func = getattr(handler, func_name)
            setattr(self.handler, func_name, func)
