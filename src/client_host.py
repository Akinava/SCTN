# -*- coding: utf-8 -*-
__author__ = 'Akinava'
__author_email__ = 'akinava@gmail.com'
__copyright__ = 'Copyright © 2019'
__license__ = 'MIT License'
__version__ = [0, 0]


import asyncio
from settings import logger
import settings
from host import Host
from client_handler import ClientHandler
from protocol import PROTOCOL
from peers import Peers
from utilit import update_obj


class Client(Host):
    def __init__(self, handler, protocol):
        #logger.debug('')
        self.swarm_status = 'in progress'
        extended_protocol = self.__extend_protocol(PROTOCOL, protocol)
        super(Client, self).__init__(handler=ClientHandler, protocol=extended_protocol)
        self.__extend_handler(handler)

    async def run(self):
        logger.debug('')
        self.listener = await self.create_listener(
            (settings.local_host,
             settings.default_port))
        swarm_task = asyncio.create_task(self.__serve_swarm())
        ping_task = asyncio.create_task(self.ping())
        await swarm_task
        await ping_task

    def __extend_protocol(self, base_protocol, client_protocol):
        #logger.debug('')
        return update_obj(base_protocol, client_protocol)

    def __extend_handler(self, handler):
        for func_name in dir(handler):
            if hasattr(self.handler, func_name):
                continue
            func = getattr(handler, func_name)
            setattr(self.handler, func_name, func)

    async def __serve_swarm(self):
        logger.debug('')
        while not self.listener.is_closing():
            if self.__has_enough_client_connections():
                await asyncio.sleep(settings.peer_timeout_seconds)
                continue
            if self.__has_server_connection():
                await asyncio.sleep(settings.peer_timeout_seconds)
                continue
            self.__find_new_connections()

    def __has_enough_client_connections(self):
        logger.debug('')
        if not self.net_pool.has_enough_connections():
            return False
        if self.swarm_status == 'in progress':
            self.swarm_status = 'done'
            self.handler().init()
        return True

    def __has_server_connection(self):
        logger.debug('')
        return len(self.net_pool.get_server_connections()) > 0

    def __find_new_connections(self):
        logger.debug('')
        if self.net_pool.has_client_connection():
            self.__connect_via_client()
        else:
            self.__connect_via_server()

    def __connect_via_client(self):
        connection = self.net_pool.get_random_client_connection()
        self.handler().do_neighbour_client_request(connection)

    def __connect_via_server(self):
        logger.debug('')
        server_data = Peers().get_random_server_from_file()
        if server_data:
            self.__do_neighbour_client_request_to_server(server_data)
            return
        raise Exception('Error: no server data in peers.json file')

    def __do_neighbour_client_request_to_server(self, server_data):
        logger.debug('')
        server_protocol = server_data['protocol']
        if server_protocol == 'udp':
            self.__udp_neighbour_client_request_to_server(server_data)
        else:
            raise Exception('Error: {} protocol handler not implemented yet'.format(server_protocol))

    def __udp_neighbour_client_request_to_server(self, server_data):
        logger.debug('')
        server_connection = self.create_connection((server_data['host'], server_data['port']))
        server_connection.set_pub_key(server_data['pub_key'])
        server_connection.type = server_data['type']
        server_connection.set_encrypt_marker(settings.request_encrypted_protocol)
        self.handler().hpn_neighbour_client_request(
            connection=server_connection
        )
