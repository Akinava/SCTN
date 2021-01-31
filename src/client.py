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

    def extend(self, handler):
        # add inherit functions from handler to self
        pass

    def define_first_swarm_peer(self, request):
        # connect to peer
        # TODO
        pass


class Client(host.UDPHost):
    async def run(self):
        self.crypto = crypt_tools.Tools()
        pass
        # get fingerprint
        # get swarm peers / connect /
        # get swarm server / connect / get swarm peer / connect
