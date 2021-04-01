# -*- coding: utf-8 -*-
__author__ = 'Akinava'
__author_email__ = 'akinava@gmail.com'
__copyright__ = 'Copyright © 2019'
__license__ = 'MIT License'
__version__ = [0, 0]


import settings
from settings import logger


class Connection:
    def __init__(self):
        self.live_points = settings.peer_live_points

    def loads(self, connection_data):
        for key, val in connection_data.items():
            if key in ['host', 'port']:
                key = 'remote_{}'.format(key)
            setattr(self, key, val)
        return self

    def is_alive(self):
        pass
        # TODO

    def set_transport(self, transport):
        self.transport = transport

    def set_protocol(self, protocol):
        self.protocol = protocol

    def set_local_port(self, local_port):
        self.local_port = local_port

    def get_remote_addr(self):
        return self.remote_host, self.remote_port

    def __eq__(self, connection):
        if self.remote_host != connection.remote_host:
            return False
        if self.remote_port != connection.remote_port:
            return False
        return True

    def set_listener(self, local_port, transport, protocol):
        self.set_protocol(protocol)
        self.set_transport(transport)
        self.set_local_port(local_port)

    def set_remote_host(self, remote_host):
        self.remote_host = remote_host

    def get_remote_host(self):
        return self.remote_host

    def set_remote_port(self, remote_port):
        self.remote_port = remote_port

    def get_remote_port(self):
        return self.remote_port

    def set_request(self, request):
        self.request = request

    def get_request(self):
        return self.request

    def get_fingerprint(self):
        return self.fingerprint

    def set_remote_addr(self, addr):
        self.set_remote_host(addr[0])
        self.set_remote_port(addr[1])

    def close_transport(self):
        self.transport.close()

    def datagram_received(self, request, remote_addr, transport):
        self.set_remote_addr(remote_addr)
        self.set_request(request)
        self.set_transport(transport)

    def set_fingerprint(self, fingerprint):
        self.fingerprint = fingerprint

    def send(self, response):
        logger.info('Connection send response')
        print(response, (self.remote_host, self.remote_port))
        self.transport.sendto(response, (self.remote_host, self.remote_port))
