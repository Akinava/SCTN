# -*- coding: utf-8 -*-
__author__ = 'Akinava'
__author_email__ = 'akinava@gmail.com'
__copyright__ = "Copyright © 2019"
__license__ = "MIT License"
__version__ = [0, 0]


from settings import logger
import settings
import host
import protocol
import crypt_tools


class ClientHandler(protocol.GeneralProtocol):
    protocol = {
        'request': 'response',
        'swarm_ping': None,
        'swarm_hello': 'swarm_servers',
        'first_swarm_peer': None,
    }

    def define_first_swarm_peer(self, request):
        # connect to peer
        # TODO
        pass


class Client(host.UDPHost):
    def __init__(self, handler):
        logger.info('Client init')
        super(Client, self).__init__(handler=ClientHandler)
        self.extend_handler(handler)
        self.init_crypt_tools()

    def init_crypt_tools(self):
        self.crypt_tools = crypt_tools.Tools()

    async def run(self):
        logger.info('Client run')

        import time
        time.sleep(5)

        # get swarm peers / connect /
        # get swarm server / connect / get swarm peer / connect

    def extend_handler(self, handler):
        logger.info('Client extend')
        self.handler.protocol.update(handler.protocol)
        for func_name in dir(handler):
            if hasattr(self.handler, func_name):
                continue
            func = getattr(handler, func_name)
            setattr(self.handler, func_name, func)
