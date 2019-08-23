# -*- coding: utf-8 -*-
import select
import socket
import errno
import threading
import time

import settings

__author__ = 'Akinava'
__author_email__ = 'akinava@gmail.com'
__copyright__ = "Copyright © 2019"
__license__ = "MIT License"
__version__ = [0, 0]


# TODO
# check MTU
# check fragmentation IP_DONTFRAGMENT


class UDPHost:
    peer_ip = 0
    peer_port = 1

    def __init__(self, handler, host, port=settings.port):
        self.port = port
        self.host = host
        self.peers = {}  # {peer_id: {'MTU': MTU, 'ip'}}
        self.__rize_peer()
        self.__handler = handler(self)

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

    def __rize_peer(self):
        self.make_socket()
        self.bind_socket()
        self.__start_listener_tread()

    def __start_listener_tread(self):
        #self.__keep_connect = True
        self.__listener_tread = threading.Thread(target = self.__listener)
        self.__listener_tread.start()

    def __listener(self):
        #print('peer run on {} port'.format(self.port))
        while True:
            msg, peer = self.socket.recvfrom(settings.buffer_size)
            self.__update_peer_timeout(peer)
            self.__check_alive_peers()
            self.__handler.handle_request(msg, peer)

    def __msg_is_pong(self, msg):
        return len(msg) == 0

    def __update_peer_timeout(self, peer):
        if not peer in self.peers:
            self.peers[peer] = {}
        self.peers[peer].update({'last_response': time.time()})
        print('peer {} update timeout with peer {}'.format(self.get_port(), peer))

    def get_ip(self):
        if not hasattr(self, 'ip'):
            self.ip = socket.gethostbyname(socket.gethostname())
        return self.ip

    def get_port(self):
        return self.socket.getsockname()[self.peer_port]

    def stop(self):
        self.socket.close()
        self.__handler.close()
        self.__listener_tread._tstate_lock = None
        self.__listener_tread._stop()

    def __del__(self):
        self.stop()
        # save peers list

    def peer_itself(self, peer):
        #print ('peer {} check peer {} is itself'.format(self.port, peer))
        if self.get_ip() == peer[self.peer_ip] and \
           self.get_port() == peer[self.peer_port]:
            return True
        return False

    def send(self, msg, peer):
        if len(msg) > settings.max_UDP_MTU:
            print ('peer {} can\'t send the message with length {}'.format(self.port, len(msg)))
        self.socket.sendto(msg, peer)

    # FIXME could be this function needed only for test
    def get_fingerprint(self):
        return self.__handler.get_fingerprint()

    def __check_alive_peers(self):
        dead_peers = []

        for peer in self.peers:
            if self.__check_if_peer_is_dead(peer):
                print('peer {} remove peer {} by timeout'.format(self.port, peer))
                dead_peers.append(peer)

        for peer in dead_peers:
            print('peer {} remove dead peer {} from list'.format(self.port, peer))
            del self.peers[peer]

        #print('peer {} has live peers'.format(self.port), self.peers)

    def __check_if_peer_is_dead(self, peer):
        #print ('check', self.get_port(), self.peers)
        peer_last_action_time = self.peers[peer]['last_response']
        #print('peer {} check if peer {} is a live, last responce {} sec ago'.format(self.port, peer, time.time() - peer_last_action_time))
        return time.time() - peer_last_action_time > settings.peer_timeout

    def remove_peer(self, peer):
        print ('peer {} remove peer {}'.format(self.get_port(), peer))
        del self.peers[peer]

    def ping(self, peer):
        self.send(b'', peer)
