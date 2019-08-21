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



class SignalHandler:
    keep_connection = b'\01'
    close_connections = b''
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

    def _get_sstn_peer_list_from_settings(self):
        sstn_peer_list = {}
        for peer in settings.hosts:
            if self._interface.peer_itself(settings.hosts[peer]) or \
               not settings.hosts[peer].get('signal') is True:
                continue
            sstn_peer_list[peer] = settings.hosts[peer]
        return sstn_peer_list


class SignalServerHandler(SignalHandler):
    def __init__(self, interface):
        # FIXME setup ecdsa if it doesn't exist / load ecdsa
        self._ecdsa = pycrypto.ECDSA()
        self._interface = interface
        # request self external port and client
        self.__thread_connect_to_swarm()

    def __thread_connect_to_swarm(self):
        connect_to_swarm_thread = threading.Thread(target = self.__connect_to_swarm)
        connect_to_swarm_thread.start()

    def __connect_to_swarm(self):
        self.__wait_interface_socket()
        sstn_peer_list = self._get_sstn_peer_list_from_settings()
        # TODO
        # connect to sstn
        # request swarm
        # stay or leave
        print ('signal server {} connect to swarm is finished'.format(self._interface.get_port()))

    def handle_request(self, msg, connection):
        if self.__check_msg_is_ping(msg):
            print ('signal server {} recive ping message from'.format(self._interface.get_port()), connection)
            self.__send_pong(connection)
            return

        self.__save_fingerprint(msg, connection)
        self.__send_swarm_list(connection)

    def __send_swarm_list(self, connection):
        msg = b''
        peers = self._interface.peers.keys()
        for peer in peers:
            msg += self.pack_ip(peer[0])                        # ip
            msg += self.pack_port(peer[1])                      # port
            msg += self._interface.peers[peer]['fingerprint']   # fingerprint

        msg += self.__sign_msg(msg)
        msg += self.__set_keep_connection()
        print ('signal server {} send swarm peers'.format(self._interface.get_port()), self._interface.peers)

    def __set_keep_connection(self):
        if len(self._interface.peers) < settings.peers_connections:
            return self.keep_connection
        return self.close_connections

    def __sign_msg(self, msg):
        msg_hash = pycrypto.sha256(msg)
        sign = self._ecdsa.sign(msg)
        sign += self._ecdsa.get_pub_key()
        return sign

    def __save_fingerprint(self, fingerprint, connection):
        self._interface.peers[connection]['fingerprint'] = fingerprint

    def __send_pong(self, connection):
        print ('signal server {} send pong to {}'.format(self._interface.get_port(), connection))
        self._interface.ping(connection)

    def __check_msg_is_ping(self, msg):
        return len(msg) == 0

    def __wait_interface_socket(self):
        while not hasattr(self._interface, '_socket_is_bound') or \
              not self._interface._socket_is_bound is True:
            time.sleep(0.1)

    def close(self):
        pass

    def __del__(self):
        # save ECDSA prv key
        pass


class SignalClientHandler(SignalHandler):
    def __init__(self, interface, ecdsa):
        # FIXME setup ecdsa if it doesn't exist / load ecdsa
        self._ecdsa = ecdsa
        self._interface = interface
        self.__thread_ping()
        self.__request_swarm_peers()

    def __request_swarm_peers(self):
        sstn_peer_list = self._get_sstn_peer_list_from_settings()
        for fingerprint in sstn_peer_list:
            sstn_connecton = (
                sstn_peer_list[fingerprint]['ip'],
                sstn_peer_list[fingerprint]['port']
            )

            print ('signal client {} send request for swarm to sstn {}'.format(self._interface.get_port(), sstn_connecton))
            self._interface.send(self.get_fingerprint(), sstn_connecton)
            self.__add_peer_as_sstn(
                sstn_connecton,
                {'fingerprint': fingerprint,
                 'signal': True,
                 'last_response': time.time()})

    def __add_peer_as_sstn(self, sstn_connection, sstn_data):
        self._interface.peers[sstn_connection] = sstn_data
        print ('siganl client {} add peer {} as sstn'.format(self._interface.get_port(), sstn_connection))

    def peer_is_sstn(self, connection):
        peer = self._interface.peers.get(connection)
        if peer is None:
            return False
        return peer.get('signal') is True

    def handle_request(self, msg, connection):
        swarm_peers = self.__unpack_swarm_peers(msg)
        for peer in swarm_peers:
            self.__make_connection_with_peer(peer)
        # if sstn send to me disconnect command:
        #   stop ping
        #   remove sstn from peers

    def __thread_ping(self):
        self.__ping_thread = threading.Thread(target = self.__ping)
        self.__ping_thread.start()

    def close(self):
        self.__ping_thread._tstate_lock = None
        self.__ping_thread._stop()

    def __ping(self):
        # in this thread ping only signal server becouse rest peers ping in the
        # main Handler
        while True:
            time.sleep(settings.ping_time)
            if len(self._interface.peers) == 0:
                self.__request_swarm_peers()

            for peer in self._interface.peers:
                peer_data = self._interface.peers[peer]
                if not peer_data.get('signal'):
                    continue

                self._interface.ping(peer)

    def __make_connection_with_peer(self, peer):
        pass
