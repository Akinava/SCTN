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
    socket_host = 0
    socket_port = 1

    def __init__(self, handler, host, port=settings.port):
        self.port = port
        self.host = host
        self.peers = {}  # {peer_id: {'MTU': MTU, 'ip'}}
        self.__rize_peer()
        self.__handler = handler(self)
        self.__tread_check_alive_peers()

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
            msg, connection = self.socket.recvfrom(settings.buffer_size)
            self.__update_peer_timeout(connection)
            self.__handler.handle_request(msg, connection)

    def __update_peer_timeout(self, connection):
        if not connection in self.peers:
            self.peers[connection] = {}
        self.peers[connection].update({'last_response': time.time()})
        print('peer {} update timeout with peer {}'.format(self.get_port(), connection), self.peers)

    def get_ip(self):
        if not hasattr(self, 'ip'):
            self.ip = socket.gethostbyname(socket.gethostname())
        return self.ip

    def get_port(self):
        return self.socket.getsockname()[self.socket_port]

    def stop(self):
        self.socket.close()
        self.__handler.close()
        self.__listener_tread._tstate_lock = None
        self.__listener_tread._stop()
        self.__check_alive_peers_thread._tstate_lock = None
        self.__check_alive_peers_thread._stop()

    def __del__(self):
        self.stop()
        # save peers list

    def peer_itself(self, peer):
        if self.get_ip() == peer['ip'] and \
           self.get_port() == peer['port']:
            return True
        return False

    def send(self, msg, connection):
        if len(msg) > settings.max_UDP_MTU:
            print ('peer {} can\'t send the message with length {}'.format(self.port, len(msg)))
        self.socket.sendto(msg, connection)

    # FIXME could be this function needed only for test
    def get_fingerprint(self):
        return self.__handler.get_fingerprint()

    def __tread_check_alive_peers(self):
        self.__check_alive_peers_thread = threading.Thread(target = self.__check_alive_peers)
        self.__check_alive_peers_thread.start()

    def __check_alive_peers(self):
        while True:
            dead_peers = []
            time.sleep(settings.ping_time)

            for peer in self.peers:
                if self.__check_if_peer_is_dead(peer):
                    dead_peers.append(peer)

            for peer in dead_peers:
                print('peer {} remove peer from list'.format(self.port), peer)
                del self.peers[peer]

            time.sleep(settings.ping_time)
            print('peer {} has live peers'.format(self.port), self.peers)

    def __check_if_peer_is_dead(self, peer):
        print ('check', self.get_port(), self.peers)
        peer_last_action_time = self.peers[peer]['last_response']
        print('peer {} check if peer {} is a live, last responce {} sec ago'.format(self.port, peer, time.time() - peer_last_action_time))
        return time.time() - peer_last_action_time > settings.peer_timeout

    def remove_connection(self, connection):
        print ('peer {} remove peer {}'.format(self.get_port(), connection))
        del self.peers[connection]

    def ping(self, connection):
        self.send(b'', connection)
