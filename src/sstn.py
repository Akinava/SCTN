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
    keep_connection_flag = b'\01'
    close_connection_flag = b''
    fingerprint_length = 32
    sign_length = 64
    open_key_length = 64
    ip_length = 4
    port_length = 2
    peer_data_length = ip_length + port_length + fingerprint_length

    def get_fingerprint(self):
        open_key = self._ecdsa.get_pub_key()
        fingerprint = pycrypto.sha256(open_key)
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
        if len(settings.peers) == 0:
            return None

        sstn_peer_list = []
        for peer in settings.peers:
            if self._interface.peer_itself(settings.peers[peer]) or \
               not settings.peers[peer].get('signal') is True:
                continue
            peer_data = settings.peers[peer]
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

                priv_key_b58 = dict_data.get('ecdsa')
                if priv_key_b58 is None:
                    return

                priv_key = pycrypto.B58().unpack(priv_key_b58)
                self._ecdsa = pycrypto.ECDSA(priv_key=priv_key)

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


    def handle_request(self, msg, peer):
        if self.__check_msg_is_ping(msg):
            print ('signal server {} recive ping message from {}'.format(self._interface.get_port(), peer))
            self.__send_pong(peer)
            return

        if not self.__check_fingerprint(msg):
            print ('signal server {} remove peer {} wrong fingerprint'.format(self._interface.get_port(), peer))
            self.__interface.remove_peer(peer)
            return

        self.__save_fingerprint(msg, peer)
        self.__save_peer_in_queue(peer)
        self.__remove_dead_peers()
        self.__send_swarm_list()

    def __remove_dead_peers(self):
        tmp_queue = []
        for peer in self.__queue:
            if not peer in self._interface.peers:
                continue
            tmp_queue.append(peer)
        self.__queue = tmp_queue

    def __save_peer_in_queue(self, peer):
        self.__queue.append(peer)

    def __check_fingerprint(self, msg):
        return len(msg) == self.fingerprint_length

    def __send_swarm_list(self):
        msg = self.__make_swarm_msq()
        if self.__oversupply_of_peers():
            leave_msg = self.__make_msg_for_leaving_peer(msg)
            leave_peer = self.__queue[0]
            self._interface.send(leave_msg, leave_peer)
            self.__remove_oldest_peer_from_queue()

        msg += self.__sign_msg(msg)
        for peer in self.__queue:
            self._interface.send(msg, peer)
        print ('signal server {} send swarm (size {} peers) to peers'.format(self._interface.get_port(), len(self._interface.peers)))

    def __make_msg_for_leaving_peer(self, msg):
        leave_msg = msg + self.close_connection_flag
        return leave_msg + self.__sign_msg(leave_msg)

    def __remove_oldest_peer_from_queue(self):
        peer = self.__queue[0]
        self.__queue = self.__queue[1:]
        print ('signal server {} remove oldest peer {} from the queue'.format(self._interface.get_port(), peer))
        self._interface.remove_peer(peer)

    def __make_swarm_msq(self):
        msg = b''
        peers = self._interface.peers.keys()
        for peer in peers:
            msg += self.pack_ip(peer[host.UDPHost.peer_host])   # ip          4
            msg += self.pack_port(peer[host.UDPHost.peer_port]) # port        2
            msg += self._interface.peers[peer]['fingerprint']   # fingerprint 32
        return msg

    def __oversupply_of_peers(self):
        return len(self._interface.peers) > settings.min_peer_connections

    def __sign_msg(self, msg):
        sign = self._ecdsa.sign(msg)
        open_key = self._ecdsa.get_pub_key()
        return sign + open_key

    def __save_fingerprint(self, fingerprint, peer):
        self._interface.peers[peer]['fingerprint'] = fingerprint

    def __send_pong(self, peer):
        print ('signal server {} send pong to {}'.format(self._interface.get_port(), peer))
        self._interface.ping(peer)

    def __check_msg_is_ping(self, msg):
        return len(msg) == 0

    def close(self):
        print ('sstn save the key')
        with open(settings.shadow_file, 'w') as shadow_file:
            priv_key = self._ecdsa.get_priv_key()
            priv_key_b58 = pycrypto.B58().pack(priv_key)
            shadow_file.write(json.dumps({
                'ecdsa': priv_key_b58
            }, indent=2))

    def __del__(self):
        self.close()


class SignalClientHandler(SignalHandler):
    """
    swarm list
    ip, port, figrerpint       x N time
    keep_connection            x could be skipped
    sign
    public key
    """
    def __init__(self, interface, ecdsa):
        # FIXME setup ecdsa if it doesn't exist / load ecdsa
        self._ecdsa = ecdsa
        self._interface = interface
        self.__thread_ping_sstn()

    def __request_swarm_peers(self):
        # if sctn has connection with swarm, request connections use current connect with the swarm
        # return
        # else... sstn

        sstn_data = self._get_rundom_sstn_peer_from_settings()
        sstn_peer = (
            sstn_data['ip'],
            sstn_data['port'])
        sstn_fingerprint = sstn_data['fingerprint']

        print ('signal client {} send request for swarm to sstn {}'.format(self._interface.get_port(), sstn_peer))
        self._interface.send(self.get_fingerprint(), sstn_peer)
        self.__save_peer(sstn_peer, sstn_fingerprint, True)

    def __save_peer(self, peer, fingerprint, signal=False):
        if not peer in self._interface.peers:
            self._interface.peers[peer] = {}
        self._interface.peers[peer]['fingerprint'] = fingerprint
        self._interface.peers[peer]['last_response'] = time.time()
        if signal is True: self._interface.peers[peer]['signal'] = True
        print ('siganl client {} add peer {}'.format(self._interface.get_port(), peer))

    def peer_is_sstn(self, peer):
        peer = self._interface.peers.get(peer)
        if peer is None:
            return False
        return peer.get('signal') is True

    def msg_is_swarm_list(self, msg):
        msg_length = (len(msg) - self.sign_length - self.open_key_length)
        keep_connection_flag = msg_length % (self.peer_data_length)
        return keep_connection_flag in [0, 1]

    def handle_request(self, sstn_msg, sstn_peer):
        if not self.__verify_sstn_open_key(sstn_msg, sstn_peer) or \
           not self.__verify_sign(sstn_msg):
            self._interface.remove_peer(sstn_peer)
            self.__request_swarm_peers()
            return

        swarm_peers = self.__unpack_swarm_peers(sstn_msg)
        self.__handle_sstn_connection(sstn_msg, sstn_peer)

        # thread for hole punching? # TODO

        for peer in swarm_peers:
            self.__make_connection_with_peer(peer)

    def __unpack_swarm_peers(self, msg):
        msg_length = (len(msg) - self.sign_length - self.open_key_length)
        peers_length = int(msg_length / self.peer_data_length)
        for peer_index in range(peers_length):
            peer_data_start = peer_index * self.peer_data_length
            peer_data_end = peer_data_start + self.peer_data_length
            peer_data = msg[peer_data_start: peer_data_end]
            ip_data, tail = self.__cut_data(peer_data, self.ip_length)
            port_data, fingerprint = self.__cut_data(tail, self.port_length)
            # TODO unpack ip_data, port_data
            peer = (ip, port)
            if self._interface.peer_itself(peer):
                continue
            self.__save_peer(peer, fingerprint)

        swarm_peers = []
        return swarm_peers

    def __handle_sstn_connection(self, sstn_msg, sstn_peer):
        recived_byte_flag_close_sstn_connection = self.__msg_has_close_connection_flag(sstn_msg)
        if recived_byte_flag_close_sstn_connection is False:
            return
        self._interface.remove_peer(sstn_peer)

    def __msg_has_close_connection_flag(self, msg):
        msg_length = len(msg) - self.open_key_length - self.sign_length
        return True if msg_length % self.peer_data_length == 1 else False

    def __verify_sstn_open_key(self, sstn_msg, sstn_peer):
        sstn_open_key = sstn_msg[-self.open_key_length: ]
        if len(sstn_open_key) != self.open_key_length:
            return False

        fingerprint = self._interface.peers[sstn_peer]['fingerprint']
        return fingerprint == pycrypto.sha256(sstn_open_key)

    def __verify_sign(self, msg):
        msg_length = len(msg) - self.open_key_length - self.sign_length
        signed_msg, tail = self.__cut_data(msg, msg_length)
        sign, open_key = self.__cut_data(tail, self.sign_length)
        ecdsa = pycrypto.ECDSA(pub_key=open_key)
        return ecdsa.check_signature(signed_msg, sign)

    def __cut_data(self, data, length):
        return data[0: length], data[length: ]

    def __thread_ping_sstn(self):
        self.__ping_sstn_thread = threading.Thread(target = self.__ping_sstn)
        self.__ping_sstn_thread.start()

    def __ping_sstn(self):
        self._wait_interface_socket()

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
        self.__ping_sstn_thread._tstate_lock = None
        self.__ping_sstn_thread._stop()
