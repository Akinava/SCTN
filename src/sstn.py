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

    def unpack_swarm_peers(self, msg):
        pass


class SignalServerHandler(SignalHandler):
    def __init__(self, interface):
        # FIXME setup ecdsa if it doesn't exist / load ecdsa
        self._ecdsa = pycrypto.ECDSA()
        self.__interface = interface
        # request self external port and client
        self.__connect_to_swarm_thread()
        self.__swarm = {}

    def __connect_to_swarm_thread(self):
        connect_to_swarm_thread = threading.Thread(target = self.__connect_to_swarm)
        connect_to_swarm_thread.start()

    def __connect_to_swarm(self):
        # TODO
        self.__wait_interface_socket()
        sstn_peer_list = self.__interface.get_sstn_peer_list_from_settings()
        # connect to sstn
        # request swarm
        # stay or leave
        print ('connect to swarm is finished')

    def handle_request(self, msg, connection):
        if self.__check_msg_is_ping(msg):
            print ('sstn got ping message')
            self.__send_pong(connection)
            return

        if self.__swarm:
            self.__send_swarm_list()
            return
        print ('sstn doesn\'t have swarm')
        self.__send_pong(connection)
        self.__add_peer_to_swarm_list()

    def __add_peer_to_swarm_list(connection):
        pass

    def __send_pong(self, connection):
        print ('sstn send pong to', connection)
        self.__interface.send(b'', connection)

    def __check_msg_is_ping(self, msg):
        return len(msg) == 0

    def __wait_interface_socket(self):
        while not hasattr(self.__interface, '_socket_is_bound') or \
              not self.__interface._socket_is_bound is True:
            time.sleep(0.1)

    def __del__(self):
        # save ECDSA prv key
        pass


class SignalClientHandler(SignalHandler):
    def __init__(self, interface):
        # FIXME setup ecdsa if it doesn't exist / load ecdsa
        self._ecdsa = pycrypto.ECDSA()
        self.__interface = interface

    def request_swarm_peers(self):
        sstn_peer_list = self.__interface.get_sstn_peer_list_from_settings()
        for peer in sstn_peer_list:
            ip = sstn_peer_list[peer]['ip']
            port = sstn_peer_list[peer]['port']
            print ('signal client, send request to sstn')
            self.__interface.send(self.__swarm_request(), (ip, port))
            self.__interface.recvfrom()

    def __swarm_request(self):
        fingerprint = self.get_fingerprint()
        ip = self.pack_ip(self.__interface.get_ip())
        port = self.pack_port(self.__interface.get_port())
        return fingerprint + ip + port

    def __check_msg_is_wait(self, msg):
        return len(msg) == 0

    def handle_request(self, msg, connection):
        if self.__check_msg_is_wait(msg):
            # run pinger
            self.__ping_thread()
            return

        swarm_peers = self.unpack_swarm_peers(msg)
        for peer in swarm_peers:
            self.__make_connection_with_peer(peer)

    def __ping_thread(self):
        pass

    def __make_connection_with_peer(self, peer):
        pass

