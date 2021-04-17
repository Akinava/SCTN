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
from utilit import unpack_stream, get_rundom_server
from connection import Connection


class ClientHandler(protocol.GeneralProtocol):
    protocol = {
        'request': 'response',
        'swarm_ping': None,
        'swarm_peer_response': 'handle_peer',
    }

    def do_swarm_request_connect(self, connection):
        logger.info('ClientHandler do_swarm_request_connect')
        print([connection.get_fingerprint(), self.crypt_tools.get_fingerprint()])
        return connection.get_fingerprint() + self.crypt_tools.get_fingerprint()

    def define_swarm_peer_response(self, connection):
        if connection.get_fingerprint() != self.unpack_swarm_peer(connection)['my_figerprint']:
            return False
        if not self.get_connect_flag(connection) in [self.disconnect_flag, self.keep_connection_flag]:
            return False
        return True

    def do_handle_peer(self, connection):
        connect_flag = self.get_connect_flag(connection)
        if connect_flag == self.disconnect_flag():
            connection.shutdown()
        neighbour_fingerprint = self.unpack_swarm_peer(connection)['neighbour_fingerprint']
        neighbour_ip = self.unpack_swarm_peer(connection)['neighbour_ip']
        neighbour_port = self.unpack_swarm_peer(connection)['neighbour_port']

        # TODO
        # save status client is pooling
        # pool treadeing to neighbour_ip in port range

    def unpack_swarm_peer(self, connection):
        response = connection.get_request()
        my_figerprint, rest = unpack_stream(response, self.crypt_tools.get_fingerprint_len())
        neighbour_fingerprint, rest = unpack_stream(rest, self.crypt_tools.get_fingerprint_len())
        addr, connect_flag = unpack_stream(rest, 6)
        ip, port = connection.loads_addr(addr)
        return {'my_figerprint': my_figerprint,
                'neighbour_fingerprint': neighbour_fingerprint,
                'neighbour_ip': ip,
                'neighbour_port': port,
                'connect_flag': connect_flag}

    def get_neighbour_addr(self):
        response[self.crypt_tools.get_fingerprint_len()*2: -1]

    def get_connect_flag(self, connection):
        return self.unpack_swarm_peer(connection)['connect_flag']


class Client(host.Host):
    def __init__(self, handler):
        logger.info('Client init')
        super(Client, self).__init__(handler=ClientHandler)
        self.extend_handler(handler)
        self.__swarm_status = 'creations'  # TODO stable

    async def run(self):
        logger.info('Client run')
        #await self.create_listener(settings.default_port)
        await self.__make_swarm()
        await self.__serve_forever()

    def __check_swarm_status_is_stable(self):
        return self.__swarm_status == 'stable'

    async def __make_swarm(self):
        logger.info('')
        while True:
            if self.has_enough_connections():
                await asyncio.sleep(settings.peer_ping_time_seconds)
            elif self.has_stable_connections():
                await self.ask_client_for_connections()
                continue
                # needs to save when it is done to avoid spamming client check all connections with status waiting or ask a new one
            elif self.has_saved_clients():
                await self.connect_to_saved_client()
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

    def has_stable_connections(self):
        logger.info('Client has_client_connections')
        # check client has two or more connection
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
            # TODO get server_connections
            # set serverv alive_points -= 1 # implementation need to be done in host class / ping
            return True
        # TODO else
        #   make new connection
        server = get_rundom_server()
        server_connection = Connection().loads(server)
        await self.send(
            connection=server_connection,
            message=self.handler().do_swarm_request_connect(server_connection),
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
