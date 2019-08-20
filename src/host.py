# -*- coding: utf-8 -*-
import select
import socket
import errno
import settings

__author__ = 'Akinava'
__author_email__ = 'akinava@gmail.com'
__copyright__ = "Copyright © 2019"
__license__ = "MIT License"
__version__ = [0, 0]


# TODO
# check fragmentation IP_DONTFRAGMENT


class UDPHost:
    def __init__(self, handler, host, port=settings.port):
        self.port = port
        self.host = host
        self.__handler = handler(self)
        self.peers = {}  # {peer_id: {'MTU': MTU, 'ip'}}

    def make_socket(self):
        self.socket = socket.socket(family=socket.AF_INET, type=socket.SOCK_DGRAM)

    def bind_socket(self):
        try:
            self.socket.bind((self.host, self.port))
            self._socket_is_bound = True
        except socket.error as e:
            if e.errno == errno.EADDRINUSE:
                print('Error: port {} is already in use'.format(self.port))
                self.port += 1
                self.bind_socket()

    def rize_server(self):
        self.make_socket()
        self.bind_socket()
        print('Info: run server on {} port'.format(self.port))
        self.__keep_connect = True
        self.recvfrom()

    def recvfrom(self):
        while self.__keep_connect:
            data, connection = self.socket.recvfrom(settings.buffer_size)
            self.__handler.handle_request(data, connection)

    def get_ip(self):
        if not hasattr(self, 'ip'):
            self.ip = socket.gethostbyname(socket.gethostname())
        return self.ip

    def get_port(self):
        return self.port

    def close(self):
        self.__keep_connect = False
        self.socket.close()

    def __del__(self):
        self.close()
        # save peers list

    def get_sstn_peer_list_from_settings(self):
        sstn_peer_list = {}
        for peer in settings.hosts:
            if self.__peer_itself(settings.hosts[peer]) or \
               not settings.hosts[peer].get('signal') is True:
                continue
            sstn_peer_list[peer] = settings.hosts[peer]
        return sstn_peer_list

    def __peer_itself(self, peer):
        if self.get_ip() == peer['ip'] and \
           self.get_port() == peer['port']:
            return True
        return False

    def send(self, msg, connection):
        self.socket.sendto(msg, connection)

    # FIXME could be this function needed only for test
    def get_fingerprint(self):
        return self.__handler.get_fingerprint()

    def rize_client(self):
        self.make_socket()
        self.__keep_connect = True
        self.__handler.request_swarm_peers()
