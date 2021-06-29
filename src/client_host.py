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
        swarm_task = asyncio.create_task(self.__serve_swarm())
        ping_task = asyncio.create_task(self.ping())
        await swarm_task
        await ping_task

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
            if self.__has_server_connection():
                await asyncio.sleep(settings.peer_timeout_seconds)
                continue
            if self.__has_enough_client_connections():
                await asyncio.sleep(settings.peer_timeout_seconds)
                continue
            self.__find_new_connections()

    def __has_enough_client_connections(self):
        logger.info('')
        return self.net_pool.has_enough_connections()

    def __has_server_connection(self):
        logger.info('')
        return len(self.net_pool.get_server_connections()) > 0

    def __find_new_connections(self):
        logger.info('')
        if self.net_pool.swarm_status_stable() and self.net_pool.has_client_connection():
            self.__connect_via_client()
        else:
            self.__connect_via_server()

    def __connect_via_client(self):
        connection = self.net_pool.get_random_client_connection()
        self.handler.do_swarm_peer_request(connection)

    def __connect_via_server(self):
        logger.info('')
        server_data = Peers().get_random_server_from_file()
        if server_data:
            self.__do_swarm_peer_request_to_server(server_data)
            return
        raise Exception('Error: no server data in peers.json file')

    def __do_swarm_peer_request_to_server(self, server_data):
        logger.info('')
        server_protocol = server_data['protocol']
        if server_protocol == 'udp':
            self.__udp_swarm_peer_request_to_server(server_data)
        else:
            raise Exception('Error: {} protocol handler not implemented yet'.format(server_protocol))

    def __udp_swarm_peer_request_to_server(self, server_data):
        logger.info('')
        connection = self.listener.copy()
        connection.set_remote_addr((server_data['host'], server_data['port']))
        connection.set_pub_key(server_data['pub_key'])
        connection.set_type(server_data['type'])
        self.net_pool.save_connection(connection)
        connection.send(self.handler(self.protocol).swarm_peer_request(receiver_connection=connection))
