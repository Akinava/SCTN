#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import time
import threading
import struct

import host
import pycrypto
import settings

__author__ = 'Akinava'
__author_email__ = 'akinava@gmail.com'
__copyright__ = "Copyright © 2019"
__license__ = "MIT License"
__version__ = [0, 0]
# Signal Server for Traversal NAT


wait = b'\00'


class SignalHandler:
    keep_connection = b'\01'
    fingerprint_length = 32
    connection_length = 6

    def get_fingerprint(self):
        pub_key = self._ecdsa.get_pub_key()
        fingerprint = pycrypto.sha256(pub_key)
        return fingerprint

    def pack_ip(self, ip):
        ip_as_num = 0
        for octet in ip.split('.'):
            ip_as_num <<= 8
            ip_as_num += int(octet)
        return struct.pack('>I', ip_as_num)

    def pack_port(self, port):
        return struct.pack('>H', port)



class SignalServerHandler(SignalHandler):
    def __init__(self, interface):
        # FIXME setup ecdsa if it doesn't exist / load ecdsa
        self._ecdsa = pycrypto.ECDSA()
        self.__interface = interface
        # request self external port and client
        self.__thread_connect_to_swarm()
        self.__swarm = {}

    def __thread_connect_to_swarm(self):
        connect_to_swarm_thread = threading.Thread(target = self.__connect_to_swarm)
        connect_to_swarm_thread.start()

    def __connect_to_swarm(self):
        self.__wait_interface_socket()
        sstn_peer_list = self.__interface.get_sstn_peer_list_from_settings()
        # TODO
        # connect to sstn
        # request swarm
        # stay or leave
        print ('signal server {} connect to swarm is finished'.format(self.__interface.get_port()))

    def handle_request(self, msg, connection):
        if self.__check_msg_is_ping(msg):
            print ('signal server {} recive ping message from'.format(self.__interface.get_port()), connection)
            self.__send_pong(connection)
            return

        if self.__swarm:
            self.__send_swarm_list()
            return

        print ('siganl server {} doesn\'t have swarm'.format(self.__interface.get_port()))
        self.__send_pong(connection)
        self.__add_peer_to_swarm_list(msg, connection)

    def __add_peer_to_swarm_list(self, fingerprint, connection):
        ip = connection[0]
        port = connection[1]
        connection_data = self.pack_ip(ip) + self.pack_port(port)
        self.__swarm[connection_data] = fingerprint
        print ('siganl server {} add peer {}:{} to swarm list'.format(self.__interface.get_port(), ip, port))

    def __send_pong(self, connection):
        print ('signal server {} send pong to'.format(self.__interface.get_port()), connection)
        self.__interface.send(b'', connection)

    def __check_msg_is_ping(self, msg):
        return len(msg) == 0

    def __wait_interface_socket(self):
        while not hasattr(self.__interface, '_socket_is_bound') or \
              not self.__interface._socket_is_bound is True:
            time.sleep(0.1)

    def close(self):
        pass

    def __del__(self):
        # save ECDSA prv key
        pass


class SignalClientHandler(SignalHandler):
    def __init__(self, interface):
        # FIXME setup ecdsa if it doesn't exist / load ecdsa
        self._ecdsa = pycrypto.ECDSA()
        self.__interface = interface
        self.__thread_ping()

    def request_swarm_peers(self):
        sstn_peer_list = self.__interface.get_sstn_peer_list_from_settings()
        for peer in sstn_peer_list:
            ip = sstn_peer_list[peer]['ip']
            port = sstn_peer_list[peer]['port']
            print ('signal client {} send request to sstn'.format(self.__interface.get_port()))
            self.__interface.send(self.get_fingerprint(), (ip, port))

    def __check_msg_is_pong(self, msg):
        return len(msg) == 0

    def handle_request(self, msg, connection):
        if self.__check_msg_is_pong(msg):
            print ('signal client {} recive pong from'.format(self.__interface.get_port()), connection)
            return

        swarm_peers = self.unpack_swarm_peers(msg)
        for peer in swarm_peers:
            self.__make_connection_with_peer(peer)

    def __thread_ping(self):
        self.__ping_thread = threading.Thread(target = self.__ping)
        self.__ping_thread.start()

    def close(self):
        self.__ping_thread._tstate_lock = None
        self.__ping_thread._stop()


    def __ping(self):
        while True:
            time.sleep(settings.ping_time)
            if len(self.__interface.peers) == 0:
                self.request_swarm_peers()
            for peer in self.__interface.peers:
                self.__interface.ping(peer)

    def __make_connection_with_peer(self, peer):
        pass
