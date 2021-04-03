# -*- coding: utf-8 -*-
__author__ = 'Akinava'
__author_email__ = 'akinava@gmail.com'
__copyright__ = 'Copyright © 2019'
__license__ = 'MIT License'
__version__ = [0, 0]


import asyncio
import settings
from settings import logger
import host
import protocol
from utilit import pack_host, pack_port


class ServerHandler(protocol.GeneralProtocol):
    protocol = {
        'request': 'response',
        'swarm_ping': None,
        'swarm_peer_request': 'swarm_peer_response',
    }

    connections_group_0 = {}
    connections_group_1 = {}

    def do_swarm_peer_response(self, connection):
        logger.info('ServerHandler swarm_peer_response')
        request_type = self.get_request_type(connection)
        if request_type == 'disconnect':
            connection.shutdown()
            return
        self.set_connection_fingerprint(connection)
        self.save_client_in_group_list(connection)
        self.send_swarm_response(connection)

    def get_request_type(self, connection):
        request_type_bin = connection.get_request()[-1]
        return self.request_type_get[request_type_bin]

    def get_swarm_list_response(self):
        swarm_list_response = b''
        for connection in self.swarm_list:
            swarm_list_response += connection.get_fingerprint()
            swarm_list_response += pack_host(connection.get_remote_host())
            swarm_list_response += pack_port(connection.get_remote_port())
        return swarm_list_response

    def set_connection_fingerprint(self, connection):
        fingerprint_beginning = self.crypt_tools.get_fingerprint_len()
        fingerprint_end = self.crypt_tools.get_fingerprint_len() * 2
        connection.set_fingerprint(connection.get_request()[fingerprint_beginning: fingerprint_end])

    def save_client_in_group_list(self, connection):
        if connection in self.connections_group_0 or connection in self.connections_group_1:
            return
        if len(self.connections_group_0) > len(self.connections_group_1):
            self.connections_group_1[connection] = {}
            return
        self.connections_group_0[connection] = {}

    def send_swarm_response(self, connection):
        neighbour_connection = self.find_neighbour(connection)
        if neighbour_connection is None:
            self.set_connection_state(connection, 'waiting')
            return
        self.set_connection_state(connection, 'in_progress')
        self.set_connection_state(neighbour_connection, 'in_progress')
        sign_message = self.make_connection_message(connection, neighbour_connection)
        neighbour_sign_message = self.make_connection_message(neighbour_connection, connection)
        connection.send(sign_message)
        neighbour_connection.send(neighbour_sign_message)

    def make_connection_message(self, connection0, connection1):
        message = connection0.set_fingerprint() + connection1.get_request() + connection1.dump_addr()
        return self.sign_message(message)

    def set_connection_state(self, connection, state):
        param = self.connections_group_0.get(connection) or self.connections_group_1.get(connection)
        param['state'] = state

    def find_neighbour(self, connection):
        request_type = self.get_request_type(connection)
        neighbour_connection = None
        if request_type == 'request_eny_peer':
            connections_group = {}
            connections_group.update(self.connections_group_0)
            connections_group.update(self.connections_group_1)
            neighbour_connection = self.find_waiting_connection(connections_group)
        if request_type == 'request_peer_from_list_0':
            neighbour_connection = self.find_waiting_connection(self.connections_group_0)
        if request_type == 'request_peer_from_list_1':
            neighbour_connection = self.find_waiting_connection(self.connections_group_1)
        return neighbour_connection

    def find_waiting_connection(self, group):
        for connection, params in group.items():
            if params.get('state') == 'waiting':
                return connection
        return None

    def sign_message(self, message):
        return self.crypt_tools.sign_message(message)


class Server(host.UDPHost):
    async def run(self):
        logger.info('Server run')
        await self.create_listener(settings.default_port)
        await self.serve_forever()


if __name__ == '__main__':
    logger.info('server start')
    server = Server(handler=ServerHandler)
    asyncio.run(server.run())
    logger.info('server shutdown')
