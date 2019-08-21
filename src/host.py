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
# check fragmentation IP_DONTFRAGMENT


class UDPHost:
    socket_host = 0
    socket_port = 1

    def __init__(self, handler, host, port=settings.port):
        self.port = port
        self.host = host
        self.__handler = handler(self)
        self.peers = {}  # {peer_id: {'MTU': MTU, 'ip'}}
        self.__rize_peer()
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
        print('peer run on {} port'.format(self.port))

    def __start_listener_tread(self):
        #self.__keep_connect = True
        self.__listener_tread = threading.Thread(target = self.__listener)
        self.__listener_tread.start()

    def __listener(self):
        #while self.__keep_connect:
        while True:
            data, connection = self.socket.recvfrom(settings.buffer_size)
            self.__update_peer_timeout(connection)
            self.__handler.handle_request(data, connection)
            '''
            try:
                self.socket.settimeout(settings.peer_timeout)
                data, connection = self.socket.recvfrom(settings.buffer_size)
                self.__update_peer_timeout(connection)
                self.__handler.handle_request(data, connection)
            except socket.timeout:
                self.__keep_connect = False
                # TODO ???
            '''

    def __update_peer_timeout(self, connection):
        self.peers[connection] = time.time()

    def get_ip(self):
        if not hasattr(self, 'ip'):
            self.ip = socket.gethostbyname(socket.gethostname())
        return self.ip

    def get_port(self):
        return self.socket.getsockname()[self.socket_port]

    def stop(self):
        #self.__keep_connect = False
        self.socket.close()
        self.__handler.close()
        self.__listener_tread._tstate_lock = None
        self.__listener_tread._stop()
        self.__check_alive_peers_thread._tstate_lock = None
        self.__check_alive_peers_thread._stop()

    def __del__(self):
        self.stop()
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
        self.__handler.request_swarm_peers()

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
            print('peer {} check live peers'.format(self.port), self.peers)

    def __check_if_peer_is_dead(self, peer):
        peer_last_action_time = self.peers[peer]
        return time.time() - peer_last_action_time > settings.peer_timeout

    def ping(self, connection):
        self.send(b'', connection)
