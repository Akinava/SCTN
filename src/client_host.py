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
        self.swarm_status = 'in progress'
        logger.info('')
        super(Client, self).__init__(handler=ClientHandler, protocol=PROTOCOL)
        self.__extend_handler(handler)
        self.__extend_protocol(protocol)

    async def run(self):
        logger.info('')
        self.listener = await self.create_listener(
            (settings.local_host,
             settings.default_port))
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
        while not self.listener.is_closing():
            if self.__has_enough_client_connections():
                await asyncio.sleep(settings.peer_timeout_seconds)
                continue
            if self.__has_server_connection():
                await asyncio.sleep(settings.peer_timeout_seconds)
                continue
            self.__find_new_connections()

    def __has_enough_client_connections(self):
        logger.info('')
        if not self.net_pool.has_enough_connections():
            return False
        if self.swarm_status == 'in progress':
            self.swarm_status = 'done'
            self.init()
        return True

    def __has_server_connection(self):
        logger.info('')
        return len(self.net_pool.get_server_connections()) > 0

    def __find_new_connections(self):
        logger.info('')
        if self.net_pool.has_client_connection():
            self.__connect_via_client()
        else:
            self.__connect_via_server()

    def __connect_via_client(self):
        connection = self.net_pool.get_random_client_connection()
        self.handler.do_neighbour_client_request(connection)

    def __connect_via_server(self):
        logger.info('')
        server_data = Peers().get_random_server_from_file()
        if server_data:
            self.__do_neighbour_client_request_to_server(server_data)
            return
        raise Exception('Error: no server data in peers.json file')

    def __do_neighbour_client_request_to_server(self, server_data):
        logger.info('')
        server_protocol = server_data['protocol']
        if server_protocol == 'udp':
            self.__udp_neighbour_client_request_to_server(server_data)
        else:
            raise Exception('Error: {} protocol handler not implemented yet'.format(server_protocol))

    def __udp_neighbour_client_request_to_server(self, server_data):
        logger.info('')
        connection = self.create_connection((server_data['host'], server_data['port']))
        connection.set_pub_key(server_data['pub_key'])
        connection.type = server_data['type']
        connection.set_encrypt_marker(settings.request_encrypted_protocol)
        handler_init = self.handler(self.protocol)
        peer_request_message = handler_init.hpn_neighbour_client_request(receiver_connection=connection)
        handler_init.send(
            message=peer_request_message,
            connection=connection,
            package_protocol_name='hpn_neighbour_client_request',
        )
