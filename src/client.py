# -*- coding: utf-8 -*-
__author__ = 'Akinava'
__author_email__ = 'akinava@gmail.com'
__copyright__ = 'Copyright © 2019'
__license__ = 'MIT License'
__version__ = [0, 0]


import asyncio
from settings import logger
import settings
import host
import protocol
import utilit
from connection import Connection


class ClientHandler(protocol.GeneralProtocol):
    protocol = {
        'request': 'response',
        'swarm_ping': None,
        'swarm_list': 'handle_swarm',
    }

    def define_swarm_list(self, connection):
        logger.info('ClientHandler define_swarm_list')
        # connect to peer
        # TODO
        pass

    def do_swarm_request_connect(self):
        logger.info('ClientHandler do_swarm_request_connect')
        return self.crypt_tools.get_fingerprint()

    def do_handle_swarm(self, connection):
        pass
        # connect to swarm
        # if swarm condition and hasattr(self, 'init'):
        #   self.init()


class Client(host.UDPHost):
    def __init__(self, handler):
        logger.info('Client init')
        super(Client, self).__init__(handler=ClientHandler)
        self.extend_handler(handler)

    async def run(self):
        logger.info('Client run')
        #await self.create_listener(settings.default_port)
        await self.serve_swarm()
        await self.serve_forever()

    async def serve_swarm(self):
        logger.info('Client serve_swarm')
        while True:
            if self.has_enough_connections():
                await asyncio.sleep(settings.peer_ping_time_seconds)
            elif self.has_client_connections():
                self.ask_client_for_connections()
                continue
                # needs to save when it is done to avoid spamming client check all connections with status waiting or ask a new one
            elif self.has_saved_clients():
                self.connect_to_saved_client()
                continue
            else:
                await self.connect_to_saved_server()

    def has_saved_clients(self):
        logger.info('Client has_saved_clients')
        # find clients from peer file
        # TODO FIXME
        return False

    def has_server_connections(self):
        logger.info('Client has_server_connections')
        # check client has connection with server
        # TODO FIXME
        return False

    def has_client_connections(self):
        logger.info('Client has_client_connections')
        # check client has connection with client
        # TODO FIXME
        return False

    def ask_client_for_connections(self):
        logger.info('Client ask_client_for_connections')
        # read clients list
        # get random
        # send request to client
        # TODO

    def connect_to_saved_client(self):
        logger.info('Client connect_to_saved_client')

    async def connect_to_saved_server(self):
        logger.info('Client connect_to_saved_server')
        if self.has_server_connections():
            # set serverv alive_points -= 1 # implementation need to be done in host class / ping
            return True
        server = utilit.get_rundom_server()
        server_connection = Connection().loads(server)
        await self.send(
            connection=server_connection,
            message=self.handler().do_swarm_request_connect(),
            local_port=settings.default_port)

    def has_enough_connections(self):
        logger.info('Client has_enough_connections')
        return len(self.connections) >= settings.peer_connections

    def extend_handler(self, handler):
        logger.info('Client extend_handler')
        object_at_handler = handler()
        self.handler.protocol.update(object_at_handler.protocol)
        for func_name in dir(object_at_handler):
            if hasattr(self.handler, func_name):
                continue
            func = getattr(handler, func_name)
            setattr(self.handler, func_name, func)
