# -*- coding: utf-8 -*-
__author__ = 'Akinava'
__author_email__ = 'akinava@gmail.com'
__copyright__ = 'Copyright © 2019'
__license__ = 'MIT License'
__version__ = [0, 0]


import asyncio
import struct
from settings import logger
import settings
import host
import protocol
from utilit import unpack_stream, get_random_server_from_file


class ClientHandler(protocol.UDPProtocol):
    disconnect_flag = b'\xff'
    keep_connection_flag = b'\x00'
    addr_info_len = 6
    port_info_len = 4

    protocol = {
        'request': 'response',
        'swarm_ping': None,
        'swarm_peer_response': 'handle_peer',
        'swarm_peer_request': 'swarm_peer_response', # TODO
    }

    def do_swarm_peer_request(self, connection):
        logger.info('')
        default_port = struct.pack('>H', settings.default_port)
        return connection.get_fingerprint() + self.crypt_tools.get_fingerprint() + default_port

    def define_swarm_peer_response(self, connection):
        if connection.get_fingerprint() != self.__unpack_swarm_peer(connection)['my_figerprint']:
            return False
        if not self.__get_connect_flag(connection) in [self.disconnect_flag, self.keep_connection_flag]:
            return False
        if not self.__check_swarm_peer_response_len(connection):
            return False
        return True

    def do_handle_peer(self, connection):
        connect_flag = self.__get_connect_flag(connection)
        if connect_flag == self.disconnect_flag():
            connection.shutdown()
        neighbour_fingerprint = self.__unpack_swarm_peer(connection)['neighbour_fingerprint']
        neighbour_ip = self.__unpack_swarm_peer(connection)['neighbour_ip']
        default_port = self.__unpack_swarm_peer(connection)['default_port']
        neighbour_port = self.__unpack_swarm_peer(connection)['neighbour_port']

        # TODO
        # save status client is pooling
        # connect to default port
        # pool treadeing to neighbour_ip in port range

    def __unpack_swarm_peer(self, connection):
        response = connection.get_request()
        my_figerprint, rest = unpack_stream(response, self.crypt_tools.get_fingerprint_len())
        neighbour_fingerprint, rest = unpack_stream(rest, self.crypt_tools.get_fingerprint_len())
        addr, rest = unpack_stream(rest, self.addr_info_len)
        default_port, connect_flag = unpack_stream(rest, self.port_info_len)
        ip, port = connection.loads_addr(addr)
        return {'my_figerprint': my_figerprint,
                'neighbour_fingerprint': neighbour_fingerprint,
                'neighbour_ip': ip,
                'neighbour_port': port,
                'default_port': default_port,
                'connect_flag': connect_flag}

    def __check_swarm_peer_response_len(self, connection):
        request_len = len(connection.get_request())
        required_len = self.crypt_tools.get_fingerprint_len() * 2 + \
            len(self.keep_connection_flag) + \
            len(self.addr_info_len) + \
            len(self.port_info_len)
        return request_len == required_len

    def __get_connect_flag(self, connection):
        return self.__unpack_swarm_peer(connection)['connect_flag']


class Client(host.UDPHost):
    def __init__(self, handler):
        logger.info('')
        super(Client, self).__init__(handler=ClientHandler)
        self.__extend_handler(handler)

    async def run(self):
        logger.info('')
        self.listener = await self.create_endpoint(settings.local_host, settings.default_port)
        await self.__serve_swarm()
        await self.serve_forever()

    def __extend_handler(self, handler):
        logger.info('')
        object_at_user_handler = handler()
        self.__update_handler_protocol(object_at_user_handler)
        self.__update_handler_functions(object_at_user_handler)

    def __update_handler_protocol(self, object_at_user_handler):
        self.handler.protocol.update(object_at_user_handler.protocol)

    def __update_handler_functions(self, object_at_user_handler):
        for func_name in dir(object_at_user_handler):
            if hasattr(self.handler, func_name):
                continue
            func = getattr(handler, func_name)
            setattr(self.handler, func_name, func)

    async def __serve_swarm(self):
        logger.info('')
        while self.alive:
            if not self.__has_enough_connections() and not self.__has_server_connection():
                await self.__find_new_connections()
            self.__init_user_client()
            await asyncio.sleep(settings.peer_ping_time_seconds)

    def __init_user_client(self):
        if not self.__has_enough_connections():
            return
        if not hasattr(self, '__swarm_state'):
            self.__swarm_state = 'created'
            self.init()

    def __has_enough_connections(self):
        logger.info('')
        return len(self.net_pool.get_all_client_connections()) >= settings.peer_connections

    def __has_server_connection(self):
        return len(self.net_pool.get_server_connections()) > 0

    async def __find_new_connections(self):
        connection = self.net_pool.get_random_client_connection()
        if not connection is None:
            self.handler.do_swarm_peer_request(connection)
        if self.__has_server_connection():
            return
        server_data = get_random_server_from_file()
        if not server_data is None:
            await self.__do_swarm_peer_request_to_server(server_data)

    async def __do_swarm_peer_request_to_server(self, server_data):
        server_protocol = server_data['protocol']
        if server_protocol == 'udp':
            await self.__udp_swarm_peer_request_to_server(server_data)
        else:
            raise Exception('Error: {} protocol handler not implemented yet'.format(server_protocol))

    async def __udp_swarm_peer_request_to_server(self, server_data):
        connection = await self.create_endpoint(
            remote_host=server_data['host'],
            remote_port=server_data['port'])
        connection.set_fingerprint(server_data['fingerprint'])
        connection.set_type(server_data['type'])
        self.handler.do_swarm_peer_request(connection)
