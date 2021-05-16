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
from connection import Connection
from utilit import unpack_stream, get_random_server_from_file


class ClientHandler(protocol.UDPProtocol):
    disconnect_flag = b'\xff'
    keep_connection_flag = b'\x00'
    addr_info_len = 6

    protocol = {
        'request': 'response',
        'swarm_ping': None,
        'swarm_peer_response': 'handle_peer',
        'swarm_peer_request': 'swarm_peer_response',
        'sstn_list_request': 'sstn_list',
        'sstn_list': 'save_sstn_list',
    }

    def do_swarm_peer_request(self, connection):
        logger.info('')
        return connection.get_fingerprint() + self.crypt_tools.get_fingerprint()

    def __do_sstn_list_request(connection):
        connection.send(self.crypt_tools.get_fingerprint() + connection.get_fingerprint())

    def define_sstn_list_request(self, connection):
        if self.crypt_tools.get_fingerprint() != self.__unpack_sstn_list_request()['my_fingerprint']:
            return False
        if self.__check_sstn_list_request_len(connection):
            return False
        return True

    def __check_sstn_list_request_len(self, connection):
        return len(connection.get_request()) == self.crypt_tools.fingerprint_length * 2

    def do_sstn_list(self, connection):
        # TODO
        pass

    def define_sstn_list(self, connection):
        # TODO
        pass

    def do_save_sstn_list(self, connection):
        # TODO
        pass

    def __unpack_sstn_list_request(self, connection):
        response = connection.get_request()
        neighbour_fingerprint, my_fingerprint = unpack_stream(response, self.crypt_tools.fingerprint_length)
        return {'neighbour_fingerprint': neighbour_fingerprint,
                'my_fingerprint': my_fingerprint}

    def define_swarm_peer_response(self, connection):
        if self.__check_my_fingerprint(connection) is False:
            return False
        if self.__check_connect_flag(connection) is False:
            return False
        if self.__check_swarm_peer_response_len(connection) is False:
            return False
        if self.__check_connection_fingerprint(connection) is False:
            return False
        if self.__check_swarm_peer_sign(connection) is False:
            return False
        return True

    def do_handle_peer(self, connection):
        connect_flag = self.__get_connect_flag(connection)
        if connect_flag == self.disconnect_flag():
            connection.shutdown()

        neighbour_fingerprint = self.__unpack_swarm_peer(connection)['neighbour_fingerprint']
        neighbour_ip = self.__unpack_swarm_peer(connection)['neighbour_ip']
        neighbour_port = self.__unpack_swarm_peer(connection)['neighbour_port']

        self.__try_connect_to_neighbour(neighbour_fingerprint, neighbour_ip, neighbour_port)
        self.__init_user_client()

    def __try_connect_to_neighbour(self, neighbour_fingerprint, neighbour_ip, neighbour_port):
        connection = self.make_connection(remote_host=neighbour_ip, remote_port=neighbour_port)
        connection.set_fingerprint(neighbour_fingerprint)
        connection.set_type('client')

        for _ in range(settings.attempt_connect):
            self.__do_sstn_list_request(connection)
            if not self.__check_connection_has_received(connection):
                continue
            self.init(connection)

        self.__set_swarm_connection_status()

    def __check_connection_has_received(self, connection):
        return not connection.last_request_is_time_out() is None

    def __set_swarm_connection_status(self):
        if hasattr(self, '__swarm_stable'):
            return
        if self.__has_enough_connections():
            self.__swarm_stable = True

    def swarm_status_stable(self):
        if hasattr(self, '__swarm_stable'):
            return True
        return False

    def __check_my_fingerprint(self, connection):
        return self.__unpack_swarm_peer(connection)['my_figerprint'] == self.crypt_tools.my_figerprint()

    def __get_connect_flag(self, connection):
        return self.__unpack_swarm_peer(connection)['connect_flag']

    def __check_connect_flag(self, connection)
        if self.__get_connect_flag(connection) in [self.disconnect_flag, self.keep_connection_flag]:
            return True
        return False

    def __check_connection_fingerprint(self, connection):
        responding_pub_key = self.__unpack_swarm_peer(connection)
        responding_fingerprint = self.crypt_tools.make_fingerprint(responding_pub_key)
        reference_fingerprint = connection.get_fingerprint()
        return responding_fingerprint == reference_fingerprint

    def __check_swarm_peer_sign(self, connection):
        return self.crypt_tools(connection.get_request())

    def __check_swarm_peer_response_len(self, connection):
        request_len = len(connection.get_request())
        required_len = self.crypt_tools.fingerprint_length * 2 + \
            len(self.addr_info_len) + \
            len(self.keep_connection_flag) + \
            self.crypt_tools.sign_length + \
            self.crypt_tools.pub_key_length
        return request_len == required_len

    def __unpack_swarm_peer(self, connection):
        response = connection.get_request()
        my_figerprint, rest = unpack_stream(response, self.crypt_tools.fingerprint_length)
        neighbour_fingerprint, rest = unpack_stream(rest, self.crypt_tools.fingerprint_length)
        addr, rest = unpack_stream(rest, self.addr_info_len)
        connect_flag, rest = unpack_stream(rest, len(self.disconnect_flag)
        sign, neighbour_pub_key = unpack_stream(rest, self.crypt_tools.sign_length)
        ip, port = connection.loads_addr(addr)
        return {'my_figerprint': my_figerprint,
                'neighbour_fingerprint': neighbour_fingerprint,
                'neighbour_ip': ip,
                'neighbour_port': port,
                'connect_flag': connect_flag,
                'sign': sign,
                'responding_pub_key': neighbour_pub_key


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
            await asyncio.sleep(settings.peer_ping_time_seconds)

    def __has_enough_connections(self):
        logger.info('')
        return len(self.net_pool.get_all_client_connections()) >= settings.peer_connections

    def __has_server_connection(self):
        return len(self.net_pool.get_server_connections()) > 0

    async def __find_new_connections(self):
        if self.handler.swarm_status_stable() and self.net_pool.has_client_connection():
            await self.__connect_via_client()
        else:
            await self.__connect_via_server()

    async def __connect_via_client(self)
        connection = self.net_pool.get_random_client_connection()
        if not connection is None:
            self.handler.do_swarm_peer_request(connection)
        if self.__has_server_connection():
            return

    async def __connect_via_server(self):
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
