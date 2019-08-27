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
    incoming_port = 3

    min_port = 0x400
    max_port = 0xffff

    def __init__(self, handler, host, port=settings.port):
        self.port = port
        self.host = host
        self.__connections = {}  # {(ip, port, incoming_port): {'MTU': MTU, 'signal': True, 'last_response': timestamp}}
        self.__listeners = {}    # {port: {'thread': listener_tread, 'alive': True}}
        self.__rize_peer()
        self.__handler = handler(self)

    def get_connections(self):
        return self.__connections.keys()

    def interface.get_connection_data(self, connection):
        return self.__connections.get(connection)

    def is_ready(self):
        while len(self.__listeners) == 0:
            time.sleep(0.1)

    def make_socket(self):
        self.socket = socket.socket(family=socket.AF_INET, type=socket.SOCK_DGRAM)

    def bind_socket(self):
        socket_is_bound = False
        port = self.port
        while socket_is_bound is False:
            try:
                self.socket.bind((self.host, port))
                socket_is_bound = True
            except socket.error as e:
                if e.errno == errno.EADDRINUSE:
                    print('Error: port {} is already in use'.format(self.port))
                    port += 1
        return port

    def __rize_peer(self):
        self.make_socket()
        port = self.bind_socket()
        self.__start_listener_tread(port)

    def __start_listener_tread(self, listener_port):
        listener_tread = threading.Thread(
            name = self.port,
            target = self.__listener,
            args=(listener_port,))
        self.__listeners[listener_port] = {'thread': listener_tread, 'alive': True}
        listener_tread.start()


    def __listener(self, listener_port):
        #print('peer run on {} port'.format(port))
        while self.__listeners[listener_port]['alive']:
            msg, peer = self.socket.recvfrom(settings.buffer_size)
            connection = peer + (listener_port,)
            self.__update_connection_timeout(connection)
            self.__check_alive_peers()
            self.__handler.handle_request(msg, connection)

    def __update_connection_timeout(self, connection):
        if not connection in self.connections:
            self.connection[connection] = {}
            self.connection[connection].update({'last_response': time.time()})
        print('peer {} update timeout with peer {}'.format(self, peer))

    def get_ip(self):
        if not hasattr(self, 'ip'):
            self.ip = socket.gethostbyname(socket.gethostname())
        return self.ip

    def __stop_listeners(self):
        for port in self.__listeners:
            self.__listeners[port]['alive'] = False

    def stop(self):
        self.socket.close()
        self.__handler.close()
        self.__stop_listeners()

    def __del__(self):
        self.stop()
        # save peers list

    def peer_itself(self, peer):
        if peer[self.peer_ip] == self.get_ip() and \
           peer[self.peer_port] in self.__listeners:
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

        # TODO shutdown listener_tread that are not used
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
