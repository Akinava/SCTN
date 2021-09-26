# -*- coding: utf-8 -*-
__author__ = 'Akinava'
__author_email__ = 'akinava@gmail.com'
__copyright__ = 'Copyright © 2019'
__license__ = 'MIT License'
__version__ = [0, 0]


import asyncio
import settings
from host import Host
from protocol import PROTOCOL
from peers import Peers
from datagram import Datagram
from utilit import update_obj, JObj, Stream
from client_handler import ClientHandler
from client_net_pool import ClientNetPool


class Client(Host):
    def __init__(self, handler, protocol):
        extended_protocol = self.__extend_protocol(PROTOCOL, protocol)
        extended_handler = self.__extend_handler(handler)
        super(Client, self).__init__(net_pool=ClientNetPool, handler=extended_handler, protocol=extended_protocol)
        self.net_pool.swarm_status = 'in progress'

    async def run(self):
        await self.create_default_listener()
        ping_task = asyncio.create_task(self.ping())
        swarm_task = asyncio.create_task(self.__serve_swarm())
        await ping_task
        await swarm_task

    def __extend_protocol(self, base_protocol, client_protocol):
        return update_obj(base_protocol, client_protocol)

    def __extend_handler(self, user_handler):
        class ExtendHandler(user_handler, ClientHandler):
            pass
        return ExtendHandler

    async def __serve_swarm(self):
        while not self.default_listener.is_closing():
            if self.net_pool.has_enough_client_connections():
                await asyncio.sleep(settings.peer_ping_time_seconds)
                continue
            if self.__has_server_connection():
                await asyncio.sleep(settings.peer_ping_time_seconds)
                continue
            self.__find_new_connections()

    def __has_server_connection(self):
        return len(self.net_pool.get_server_connections()) > 0

    def __find_new_connections(self):
        if self.net_pool.has_client_connection():
            self.__connect_via_client()
        else:
            self.__connect_via_server()

    def __connect_via_client(self):
        connection = self.net_pool.get_random_client_connection()
        self.handler().do_neighbour_client_request(connection)

    def __connect_via_server(self):
        server_data = Peers().get_random_server_from_file()
        if server_data:
            self.__do_neighbour_client_request_to_server(server_data)
            return
        raise Exception('Error: no server data in peers.json file')

    def __do_neighbour_client_request_to_server(self, server_data):
        server_protocol = server_data['protocol']
        if server_protocol == 'udp':
            self.__udp_neighbour_client_request_to_server(server_data)
        else:
            raise Exception('Error: {} protocol handler not implemented yet'.format(server_protocol))

    def __udp_neighbour_client_request_to_server(self, server_data):
        server_connection = self.__make_server_connection(server_data)
        request = Datagram(connection=server_connection)
        request.set_package_protocol(JObj({'response': 'hpn_neighbours_client_request'}))
        Stream().run_stream(target=self.handler().hpn_neighbours_client_request, request=request)

    def __make_server_connection(self, server_data):
        server_connection = self.net_pool.create_connection((server_data['host'], server_data['port']), self.default_listener)
        server_connection.set_pub_key(server_data['pub_key'])
        server_connection.set_encrypt_marker(settings.request_encrypted_protocol)
        server_connection.type = server_data['type']
        return server_connection
