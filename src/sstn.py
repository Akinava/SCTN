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
    keep_connection_flag = b''
    close_connection_flag = b'\01'
    fingerprint_length = 32
    sign_length = 64
    open_key_length = 64
    ip_length = 4
    port_length = 2
    peer_data_length = ip_length + port_length + fingerprint_length

    def _setup_ecdsa(self):
        self._ecdsa = None
        self._get_ecdsa_from_file()
        if self._ecdsa is None:
            self._ecdsa = pycrypto.ECDSA()

    def _get_ecdsa_from_file(self):
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

    def _get_connection_data(self, connection):
        return self._interface.get_connection_data(connection)

    def _wait_interface_socket(self):
        self._interface.is_ready()

    def get_fingerprint(self):
        open_key = self._ecdsa.get_pub_key()
        fingerprint = pycrypto.sha256(open_key)
        return fingerprint

    def _get_rundom_sstn_peer_from_settings(self):
        if len(settings.peers) == 0:
            return None

        sstn_peer_list = []
        for fingerprint in settings.peers:
            peer_data = settings.peers[fingerprint]
            peer = (peer_data['ip'], peer_data['port'])

            if self._interface.peer_itself(peer) or \
               not peer_data.get('signal') is True:
                continue

            peer_data['fingerprint'] = fingerprint
            sstn_peer_list.append(peer_data)

        if len(sstn_peer_list) == 0:
            return None

        random.shuffle(sstn_peer_list)
        return sstn_peer_list[0]

    def _save_connection(self, fingerprint, connection, signal=False):
        if not fingerprint in self._peers:
            self._peers[fingerprint] = {'connections': []}
        self._peers[fingerprint]['connections'].append(connection)
        if signal:
            self._peers[fingerprint]['signal'] = True
        print ('siganl peer {} add {}'.format(self._interface, connection))

    def _remove_peer(self, fingerprint):
        if fingerprint in self._peers:
            del self._peers[fingerprint]

    def _msg_is_ping(self, msg):
        return len(msg) == 0


class SignalServerHandler(SignalHandler):
    def __init__(self, interface):
        self._setup_ecdsa()
        self._interface = interface
        self._wait_interface_socket()
        self._peers = {}
        # request self external port and client
        self.__thread_connect_to_swarm()
        self.__queue = []


    def __thread_connect_to_swarm(self):
        connect_to_swarm_thread = threading.Thread(target = self.__connect_to_swarm)
        connect_to_swarm_thread.start()

    def __connect_to_swarm(self):
        sstn_peer = self._get_rundom_sstn_peer_from_settings()

        if sstn_peer is None:
            print ('signal server {} no sstn to request a swarm'.format(self._interface))
            return

        # TODO
        # connect to sstn
        # request swarm
        # stay or leave
        print ('signal server {} connect to swarm is finished'.format(self._interface.get_port()))

    def __pack_ip(self, ip):
        ip_data = b''
        for octet in ip.split('.'):
            ip_data += chr(int(octet)).encode('utf8')
        return ip_data

    def __pack_port(self, port):
        return struct.pack('>H', port)

    def __pack_peer(self, peer):
        return self.__pack_ip(peer[host.UDPHost.peer_ip]) + \
               self.__pack_port(peer[host.UDPHost.peer_port])

    def handle_request(self, msg, connection):
        if self._msg_is_ping(msg):
            print ('signal server {} recive ping message from {}'.format(self, connection))
            self.__send_pong(connection)
            return

        if not self.__check_hello(msg):
            print ('signal server {} remove peer {} wrong fingerprint'.format(self, connection))
            self.__interface.remove_connection(connection)
            return

        self._save_connection(msg, connection)
        self.__remove_dead_connections()
        # TODO what need to do if peer has the same fingerprint ???
        self.__add_in_queue(connection)
        self.__send_swarm_list()

    def __remove_dead_connections(self):
        dead_peers = []
        for fingerprint in self._peers:
            connection = self._peers[fingerprint]['connections'][-1]
            connection_data = self._interface.get_connection_data(connection)
            if connection_data is None:
                dead_peers.append(connection)
                self.__remove_connection_from_queue(connections)
            else:
                self._peers[fingerprint]['connections'] = [connection]

        for fingerprint in dead_peers:
            self._remove_peer(fingerprint)

    def __remove_connection_from_queue(self, connection):
        if connection in self.__queue:
            self.__queue.remove(connection)

    def __add_in_queue(self, connection):
        self.__queue.append(connection)

    def __check_hello(self, msg):
        return len(msg) == self.fingerprint_length

    def __send_pong(self, connection):
        print ('signal server {} send pong to {}'.format(self, connection))
        self._interface.ping(connection)

    def __send_swarm_list(self):
        msg = self.__make_swarm_msg()

        if self.__oversupply_of_peers():
            leave_msg = msg + self.close_connection_flag
            leave_msg = self.__sign_msg(leave_msg) + leave_msg
            leave_peer = self.__queue[0]
            self._interface.send(leave_msg, leave_peer)
            self.__remove_oldest_peer_from_queue()

        msg = self.__sign_msg(msg) + msg
        for peer in self.__queue:
            self._interface.send(msg, peer)
        print ('signal server {} send swarm (size {} peers) to peers'.format(self._interface.get_port(), len(self._interface.peers)))

    def __remove_oldest_peer_from_queue(self):
        peer = self.__queue[0]
        self.__queue = self.__queue[1:]
        print ('signal server {} remove oldest peer {} from the queue'.format(self._interface.get_port(), peer))
        self._interface.remove_peer(peer)

    def __make_swarm_msg(self):
        msg = b''
        # revert self._peers  {connection: fingerprint}
        # TODO
        peers = self._interface.peers.keys()
        for peer in peers:
            msg += self.__pack_peer(peer)                   # ip           4
            msg += self._get_peer_data(peer)['fingerprint'] # fingerprint 32
        return msg

    def __oversupply_of_peers(self):
        return len(self._interface.peers) > settings.min_peer_connections

    def __sign_msg(self, msg):
        sign = self._ecdsa.sign(msg)
        open_key = self._ecdsa.get_pub_key()
        return sign + open_key

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
    def __init__(self, interface, external_handler):
        self._ecdsa = pycrypto.ECDSA()    # FIXME ECDSA
        #self._setup_ecdsa()              # FIXME ECDSA
        self._interface = interface
        self._peers = {}                  # {fingerprint: {'signal': True, 'connections': [peer, connection]}}
        self.__handler = external_handler
        self.__reload_external_handler_methods()
        self.__thread_ping_sstn()

    def __reload_external_handler_methods(self):
        self.__external_handle_request = self.__handler.handle_request
        self.__handler.handle_request = self.handle_request

    def __request_swarm_peers(self):
        # if sctn has connection with swarm or list of swarm peers,
        #   request connections use current connect with the swarm
        #   return
        # else... sstn

        sstn_data = self._get_rundom_sstn_peer_from_settings()
        sstn_peer = (
            sstn_data['ip'],
            sstn_data['port'])
        connection = self._interface.set_peer_connection(sstn_peer)
        sstn_fingerprint = sstn_data['fingerprint']
        self.__send_hello(connection)
        self._save_connection(sstn_fingerprint, connection, True)
        print ('signal client {} send request for swarm to sstn {}'.format(self._interface, connection))

    def __send_hello(self, connection):
        self._interface.send(self.get_fingerprint(), connection)

    def __noop(self, msg, peer):
        return True

    def handle_request(self, msg, connection):
        print ('SignalClientHandler.handle_request')
        func = self.__define_request_type(msg, connection)
        if not func is None and func(msg, connection) is True:
            return
        self.__external_handle_request(msg, connection)

    def __define_request_type(self, msg, connection):
        if self._msg_is_ping(msg):
            return self.__noop

        if self.__msg_is_swarm_list(msg):
            return self.__handle_swarm_list

        if self.__msg_is_hello(msg):
            return self.__handle_hello

        return None

    def __msg_is_hello(self, msg):
        return len(msg) == self.fingerprint_length

    def __msg_is_swarm_list(self, msg):
        msg_length = (len(msg) - self.sign_length - self.open_key_length)
        keep_connection_flag = msg_length % (self.peer_data_length)
        return keep_connection_flag in [0, 1]

    def __handle_hello(self, msg, connection):
        # check fingeprint from sstn and from hello msg
        # save peer
        return True

    def __handle_swarm_list(self, msg, connection):
        if not self.__verify_sstn_open_key(msg, peer) or \
           not self.__verify_sign(msg):
            self._interface.remove_peer(peer)
            self.__request_swarm_peers()
            print ('signal client {} bed mesg from sstn {}'.format(self._interface.get_port(), peer))
            return False

        self.__swarm_peers += self.__unpack_swarm_peers(msg)
        self.__handle_connection(msg, peer)
        self.__thread_connect_to_swarm()
        return True

    def __thread_connect_to_swarm(self):
        if hasattr(self, '__connect_to_swarm_thread') and self.__connect_to_swarm_thread.isAlive():
            return
        self.__connect_to_swarm_thread = threading.Thread(target = self.__connect_to_swarm)
        self.__connect_to_swarm_thread.start()

    def __connect_to_swarm(self):
        # if first peer itself connect to last peer from the list
        # if last peer connect to first peer from the list
        """
        min_peer_connections 3

        step 0
        peer 0

        step 1
        peer 0     -> peer 1 / keep sstn conn
        peer 1     -> peer 0 / keep sstn conn

        step 2
        peer 0 1   -> peer 2 / keep sstn conn
        peer 1 0             / keep sstn conn
        peer 2     -> peer 0 / keep sstn conn

        step 3
        peer 0 1 2 -> peer 3 / close sstn conn
        peer 1 0             / keep sstn conn
        peer 2 0
        peer 3     -> peer 0 / keep sstn conn

        step 4
        peer 1 0   -> peer 4 / close sstn conn
        peer 2 0             / keep sstn conn
        peer 3 0             / keep sstn conn
        peer 4     -> peer 1 / keep sstn conn

        step ...
        """
        for peer in self.__swarm_peers:
            self.__connect_to_peer(peer)

    def __connect_to_peer(self, peer):
        connection = self._interface.set_peer_connection(peer)
        self.__send_hello(connection)
        # increase attempt counter for peer
        # wait timeout try again
        # if no connection:
        #   do UDP hole pinching
        #   UDP hole pinching can be only if that peer came sstn
        print ('signal client {} try connect to {}'.format(self._interface, connection))

    def __unpack_swarm_peers(self, msg):
        swarm_peers = []
        _, msg = self.__cut_data(msg, self.sign_length + self.open_key_length)
        while len(msg) >= (self.ip_length + self.port_length):
            peer_data, msg = self.__cut_data(msg, self.ip_length + self.port_length)
            fingerprint, msg = self.__cut_data(msg, self.fingerprint_length)
            peer = self.__unpack_peer(peer_data)
            self._save_peer(peer, fingerprint)
            swarm_peers.append(peer)

        return swarm_peers

    def __unpack_peer(self, peer_data):
        ip_data, port_data = self.__cut_data(peer_data, self.ip_length)
        ip = self.__unpack_ip(ip_data)
        port = self.__unpack_port(port_data)
        return (ip, port)

    def __unpack_ip(self, ip_data):
        ip_list = []
        for octet in ip_data:
            ip_list.append(str(octet))
        return '.'.join(ip_list)

    def __unpack_port(self, port_data):
        return struct.unpack('>H', port_data)[0]

    def __handle_connection(self, sstn_msg, sstn_peer):
        recived_byte_flag_close_sstn_connection = self.__msg_has_close_connection_flag(sstn_msg)
        if recived_byte_flag_close_sstn_connection is False:
            return
        self._interface.remove_peer(sstn_peer)

    def __msg_has_close_connection_flag(self, msg):
        msg_length = len(msg) - self.open_key_length - self.sign_length
        return True if msg_length % self.peer_data_length == 1 else False

    def __verify_sstn_open_key(self, sstn_msg, sstn_peer):
        sstn_open_key = sstn_msg[self.sign_length: self.sign_length + self.open_key_length]
        if len(sstn_open_key) != self.open_key_length:
            return False
        fingerprint = self._get_peer_data(sstn_peer)['fingerprint']
        return fingerprint == pycrypto.sha256(sstn_open_key)

    def __verify_sign(self, msg):
        sign, tail = self.__cut_data(msg, self.sign_length)
        open_key, signed_msg = self.__cut_data(tail, self.open_key_length)
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
            if len(self._interface.get_connections()) == 0:
                self.__request_swarm_peers()

            for connection in self._interface.get_connections():
                peer_data = self._get_peer_data(peer)
                if not peer_data.get('fingerprint'):
                    continue

                if time.time() - peer_data['last_response'] < settings.ping_time:
                    continue

                self._interface.ping(peer)
            time.sleep(settings.ping_time)

    def close(self):
        self.__ping_sstn_thread._tstate_lock = None
        self.__ping_sstn_thread._stop()


if __name__ == "__main__":
    print('start sstn')
    signal_server = host.UDPHost(handler=SignalServerHandler, host='', port=10002)

    try:
        while True:
            time.sleep(5)
    except KeyboardInterrupt:
        signal_server.stop()

    print('stop sstn')
