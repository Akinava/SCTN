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
    keep_connect_flag = chr(0).encode()
    disconnect_flag = chr(1).encode()

    protocol = {
        'request': 'response',
        'swarm_ping': None,
        'swarm_request_connect': 'swarm_list',
    }

    current_group = 0

    swarm_clients = {}
    clients_group_0 = []
    clients_group_1 = []

    def do_swarm_list(self, connection):
        logger.info('ServerHandler do_swarm_list')
        self.set_connection_fingerprint(connection)
        self.add_swarm_client(connection)
        self.send_swarm_response(connection)


    def get_swarm_list_response(self):
        swarm_list_response = b''
        for connection in self.swarm_list:
            swarm_list_response += connection.get_fingerprint()
            swarm_list_response += pack_host(connection.get_remote_host())
            swarm_list_response += pack_port(connection.get_remote_port())
        return swarm_list_response

    def set_connection_fingerprint(self, connection):
        connection.set_fingerprint(connection.get_request())

    def add_swarm_client_in_list(self, connection):
        # TODO
        pass

    def send_swarm_response(self, connection):
        # TODO
        pass

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
