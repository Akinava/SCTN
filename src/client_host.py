# -*- coding: utf-8 -*-
__author__ = 'Akinava'
__author_email__ = 'akinava@gmail.com'
__copyright__ = 'Copyright © 2019'
__license__ = 'MIT License'
__version__ = [0, 0]


import asyncio
from settings import logger
import settings
from host import UDPHost
from client_handler import ClientHandler
from client_protocol import PROTOCOL as ClientProtocol
from connection import Peers, Connection
from utilit import update_obj


class Client(UDPHost):
    def __init__(self, handler, protocol):
        logger.info('')
        super(Client, self).__init__(handler=ClientHandler, protocol=ClientProtocol)
        self.__extend_handler(handler)
        self.__extend_protocol(protocol)

    async def run(self):
        logger.info('')
        self.listener = await self.create_endpoint(local_addr=(settings.local_host, settings.default_port))
        await self.__serve_swarm()
        await self.serve_forever()

    def __extend_protocol(self, protocol):
        self.protocol = update_obj(protocol, self.protocol)

    def __extend_handler(self, handler):
        for func_name in dir(handler):
            if hasattr(self.handler, func_name):
                continue
            func = getattr(handler, func_name)
            setattr(self.handler, func_name, func)

    async def __serve_swarm(self):
        logger.info('')
        while self.listener.is_alive():
            if not self.__has_enough_client_connections() and not self.__has_server_connection():
                await self.__find_new_connections()
            await asyncio.sleep(settings.peer_ping_time_seconds)

    def __has_enough_client_connections(self):
        logger.info('')
        return self.net_pool.has_enough_connections()

    def __has_server_connection(self):
        return len(self.net_pool.get_server_connections()) > 0

    async def __find_new_connections(self):
        logger.info('')
        if self.net_pool.swarm_status_stable() and self.net_pool.has_client_connection():
            await self.__connect_via_client()
        else:
            await self.__connect_via_server()

    async def __connect_via_client(self):
        connection = self.net_pool.get_random_client_connection()
        if not connection is None:
            self.handler.do_swarm_peer_request(connection)
        if self.__has_server_connection():
            return

    async def __connect_via_server(self):
        logger.info('')
        server_data = Peers().get_random_server_from_file()
        if not server_data is None:
            await self.__do_swarm_peer_request_to_server(server_data)

    async def __do_swarm_peer_request_to_server(self, server_data):
        logger.info('')
        server_protocol = server_data['protocol']
        if server_protocol == 'udp':
            await self.__udp_swarm_peer_request_to_server(server_data)
        else:
            raise Exception('Error: {} protocol handler not implemented yet'.format(server_protocol))

    async def __udp_swarm_peer_request_to_server(self, server_data):
        logger.info('')
        # connection = await self.create_endpoint(
        #     remote_addr=(server_data['host'], server_data['port']))
        connection = self.listener.copy()
        connection.set_remote_addr((server_data['host'], server_data['port']))
        connection.set_fingerprint(server_data['fingerprint'])
        connection.set_type(server_data['type'])
        connection.send(self.handler(self.protocol).swarm_peer_request(receiver_connection=connection))
