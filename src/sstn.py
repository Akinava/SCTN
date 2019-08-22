#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import time
import threading
import struct
import random
import os
import json

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
    sign_length = 64
    open_key_length = 64
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

    def _get_rundom_sstn_peer_from_settings(self):
        if len(settings.hosts) == 0:
            return None

        sstn_peer_list = []
        for peer in settings.hosts:
            if self._interface.peer_itself(settings.hosts[peer]) or \
               not settings.hosts[peer].get('signal') is True:
                continue
            peer_data = settings.hosts[peer]
            peer_data['fingerprint'] = peer
            sstn_peer_list.append(peer_data)
        random.shuffle(sstn_peer_list)
        return sstn_peer_list[0]

    def _wait_interface_socket(self):
        while not hasattr(self._interface, '_socket_is_bound') or \
              not self._interface._socket_is_bound is True:
            time.sleep(0.1)


class SignalServerHandler(SignalHandler):
    def __init__(self, interface):
        self.__setup_ecdsa()
        self._interface = interface
        # request self external port and client
        self.__thread_connect_to_swarm()
        self.__queue = []

    def __setup_ecdsa(self):
        self._ecdsa = None
        self.__get_ecdsa_from_file()
        if self._ecdsa is None:
            self._ecdsa = pycrypto.ECDSA()

    def __get_ecdsa_from_file(self):
        if os.path.isfile(settings.shadow_file):
            with open(settings.shadow_file) as shadow_file:
                shadow_data = shadow_file.read()

                try:
                    dict_data = json.loads(shadow_data)
                except json.decoder.JSONDecodeError:
                    return

                key_b58 = dict_data.get('ecdsa')
                if key_b58 is None:
                    return

                key = pycrypto.B58().unpack(key_b58)
                self._ecdsa = pycrypto.ECDSA(priv_key=key)

    def __thread_connect_to_swarm(self):
        connect_to_swarm_thread = threading.Thread(target = self.__connect_to_swarm)
        connect_to_swarm_thread.start()

    def __connect_to_swarm(self):
        self._wait_interface_socket()
        sstn_peer = self._get_rundom_sstn_peer_from_settings()
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

        if not self.__check_fingerprint(msg):
            self.__interface.remove_connection(connection)
            return

        self.__save_fingerprint(msg, connection)
        self.__save_peer_in_queue(connection)
        self.__remove_dead_peers()
        self.__send_swarm_list()

    def __remove_dead_peers(self):
        tmp_queue = []
        for peer in self.__queue:
            if not peer in self._interface.peers:
                continue
            tmp_queue.append(peer)
        self.__queue = tmp_queue

    def __save_peer_in_queue(self, connection):
        self.__queue.append(connection)

    def __check_fingerprint(self, msg):
        return len(msg) == self.fingerprint_length

    def __send_swarm_list(self):
        msg = self.__make_swarm_msq()
        if self.__oversupply_of_connections():
            leave_msg = self.__make_msg_for_leaving_peer(msg)
            leave_peer = self.__queue[0]
            self._interface.send(leave_msg, leave_peer)
            self.__remove_peer()

        msg += self.__sign_msg(msg)
        for peer in self.__queue:
            self._interface.send(msg, peer)
        print ('signal server {} send swarm {} peers to peers'.format(self._interface.get_port(), len(self._interface.peers)))

    def __make_msg_for_leaving_peer(self, msg):
        leave_msg = msg + self.close_connections
        return leave_msg + self.__sign_msg(leave_msg)

    def __remove_peer(self):
        peer = self.__queue[0]
        self.__queue = self.__queue[1:]
        self._interface.remove_connection(peer)

    def __make_swarm_msq(self):
        msg = b''
        peers = self._interface.peers.keys()
        for peer in peers:
            msg += self.pack_ip(peer[0])                      # ip          4
            msg += self.pack_port(peer[1])                    # port        2
            msg += self._interface.peers[peer]['fingerprint'] # fingerprint 32
        return msg

    def __oversupply_of_connections(self):
        return len(self._interface.peers) < settings.min_peer_connections

    def __sign_msg(self, msg):
        msg_hash = pycrypto.sha256(msg)
        sign = self._ecdsa.sign(msg_hash)
        pub_key = self._ecdsa.get_pub_key()
        return sign + pub_key

    def __save_fingerprint(self, fingerprint, connection):
        self._interface.peers[connection]['fingerprint'] = fingerprint

    def __send_pong(self, connection):
        print ('signal server {} send pong to {}'.format(self._interface.get_port(), connection))
        self._interface.ping(connection)

    def __check_msg_is_ping(self, msg):
        return len(msg) == 0

    def close(self):
        print ('sstn save the key')
        with open(settings.shadow_file, 'w') as shadow_file:
            key = self._ecdsa.get_priv_key()
            key_b58 = pycrypto.B58().pack(key)
            shadow_file.write(json.dumps({
                'ecdsa': key_b58
            }, indent=2))

    def __del__(self):
        self.close()


class SignalClientHandler(SignalHandler):
    def __init__(self, interface, ecdsa):
        # FIXME setup ecdsa if it doesn't exist / load ecdsa
        self._ecdsa = ecdsa
        self._interface = interface
        self.__thread_ping()

    def __request_swarm_peers(self):
        # if sctn has connection with swarm, request connections use current connect with the swarm
        # return
        # else... sstn

        sstn_peer = self._get_rundom_sstn_peer_from_settings()
        sstn_connecton = (
            sstn_peer['ip'],
            sstn_peer['port'])

        print ('signal client {} send request for swarm to sstn {}'.format(self._interface.get_port(), sstn_connecton))
        self._interface.send(self.get_fingerprint(), sstn_connecton)
        self.__add_peer_as_sstn(
            sstn_connecton,
            {'fingerprint': sstn_peer['fingerprint'],
             'signal': True,
             'last_response': time.time()})

    def __add_peer_as_sstn(self, sstn_connection, sstn_data):
        if not sstn_connection in self._interface.peers:
            self._interface.peers[sstn_connection] = {}
        self._interface.peers[sstn_connection].update(sstn_data)
        print ('siganl client {} add peer {} as sstn'.format(self._interface.get_port(), sstn_connection), self._interface.peers)

    def peer_is_sstn(self, connection):
        peer = self._interface.peers.get(connection)
        if peer is None:
            return False
        return peer.get('signal') is True

    def msg_is_swarm_list(self, msg):
        swarm_list_and_keep_connection_flag_length = (len(msg) - self.sign_length - self.open_key_length)
        keep_connection_flag = swarm_list_and_keep_connection_flag_length % (self.connection_length + self.fingerprint_length)
        return keep_connection_flag in [0, 1]

    def handle_request(self, msg, connection):
        swarm_peers = self.__unpack_swarm_peers(msg)
        for peer in swarm_peers:
            self.__make_connection_with_peer(peer)
        # if sstn send to me disconnect command:
        #   stop ping
        #   remove sstn from peers

    def __unpack_swarm_peers(self, msg):
        pass

    def __thread_ping(self):
        self.__ping_thread = threading.Thread(target = self.__ping)
        self.__ping_thread.start()

    def __ping(self):
        self._wait_interface_socket()
        # in this thread ping only signal server becouse rest peers ping in the
        # main Handler
        while True:
            if len(self._interface.peers) == 0:
                self.__request_swarm_peers()

            for peer in self._interface.peers:
                peer_data = self._interface.peers[peer]
                if not peer_data.get('signal'):
                    continue

                self._interface.ping(peer)
            time.sleep(settings.ping_time)

    def __make_connection_with_peer(self, peer):
        pass

    def close(self):
        self.__ping_thread._tstate_lock = None
        self.__ping_thread._stop()
