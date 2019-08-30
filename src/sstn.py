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
        self._read_ecdsa_from_shadow()
        if self._ecdsa is None:
            self._ecdsa = pycrypto.ECDSA()

    def _read_ecdsa_from_shadow(self):
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
            peer_data = settings.peers[fingerprint].copy()
            if self._interface.peer_itself(peer_data) or \
               not peer_data.get('signal') is True:
                continue

            peer_data['fingerprint'] = fingerprint
            sstn_peer_list.append(peer_data)

        if len(sstn_peer_list) == 0:
            return None

        random.shuffle(sstn_peer_list)
        return sstn_peer_list[0]

    def _save_connection(self, fingerprint, connection, signal=False):
        self._interface.update_connection_timeout(connection)
        if fingerprint not in self._peers:
            self._peers[fingerprint] = {'connections': []}
        self._peers[fingerprint]['connections'].append(connection)
        if signal:
            self._peers[fingerprint]['signal'] = True
        print ('siganl peer {} add {}'.format(self._interface, connection))

    def _remove_peer(self, fingerprint):
        connections = self._peers[fingerprint]['connections']
        for connection in connections:
            self._interface.remove_connection(connection)
        del self._peers[fingerprint]

    def _get_peer_connections(self, fingerprint):
        return self._peers.get(fingerprint, {}).get('connections', [])

    def _msg_is_ping(self, msg):
        return len(msg) == 0

    def _clean_connections(self):
        for fingerprint in self._peers:
            connections = self._get_peer_connections(fingerprint)
            connections_tmp = []
            for connection in connections:
                if connection not in self._interface.get_connections():
                    continue
                connections_tmp.append(connection)

            if len(connections_tmp) == 0:
                self._remove_peer(fingerprint)
            else:
                self._peers[fingerprint]['connection'] = connections_tmp


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
        connect_to_swarm_thread = threading.Thread(target=self.__connect_to_swarm)
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

    def __pack_peer(self, fingerprint):
        connection = self._peers[fingerprint]['connections'][0]
        return self.__pack_ip(connection[host.UDPHost.peer_ip]) + \
            self.__pack_port(connection[host.UDPHost.peer_port])

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
        self.__put_in_queue(msg)
        self.__clean_old_connections()
        self._clean_connections()
        self.__send_swarm_list()

    def __clean_old_connections(self):
        old, new = 0, 1
        for fingerprint in self._peers:
            connections = self._peers[fingerprint]['connections']
            if len(connections) == 1:
                continue
            self._interface.remove_connection(connections[old])
            self._peers[fingerprint]['connections'] = [connections[new]]

    def __put_in_queue(self, fingerprint):
        if fingerprint in self.__queue:
            self.__queue.remove(fingerprint)
        self.__queue.append(fingerprint)

    def __check_hello(self, msg):
        return len(msg) == self.fingerprint_length

    def __send_pong(self, connection):
        print ('signal server {} send pong to {}'.format(self, connection))
        self._interface.ping(connection)

    def __send_swarm_list(self):
        old = 0
        msg = self.__make_swarm_msg()

        if self.__oversupply_of_peers():
            leave_msg = self.__add_close_connection_flag(msg)
            leave_msg = self.__sign_msg(leave_msg) + leave_msg
            leave_peer_fingerprint = self.__queue[old]
            leave_peer_connection = self._get_peer_connections(leave_peer_fingerprint)[old]
            self._interface.send(leave_msg, leave_peer_connection)
            self._remove_peer(leave_peer_fingerprint)

        msg = self.__sign_msg(msg) + msg
        for fingerprint in self.__queue:
            connection = self._get_peer_connections(fingerprint)[old]
            self._interface.send(msg, connection)
        print ('signal server {} send swarm (size {} peers) to peers'.format(self, len(self.__queue)))

    def __add_close_connection_flag(self, msg):
        return msg + self.close_connection_flag

    def __make_swarm_msg(self):
        msg = b''
        for fingerprint in self.__queue:
            msg += self.__pack_peer(fingerprint)  # ip + port    6
            msg += fingerprint                    # fingerprint 32
        return msg

    def __oversupply_of_peers(self):
        return len(self.__queue) > settings.min_peer_connections

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
        # self._setup_ecdsa()             # FIXME ECDSA
        self._interface = interface
        self._peers = {}                  # {fingerprint: {'signal': True, 'connections': [peer, connection]}}
        self.__handler = external_handler
        self.__reload_external_handler_methods()
        self.__thread_ping_sstn()
        self.__connection_threads = {}

    def __reload_external_handler_methods(self):
        self.__external_handle_request = self.__handler.handle_request
        self.__handler.handle_request = self.handle_request

    def __request_swarm_peers(self):
        # if sctn has connection with swarm or list of swarm peers,
        #   request connections use current connect with the swarm
        #   return
        # else... sstn
        sstn_data = self._get_rundom_sstn_peer_from_settings()
        if sstn_data is None:
            print ('signal client {} no sstn in peers file'.format(self._interface))
            return
        sstn_peer = (
            sstn_data['ip'],
            sstn_data['port'])
        connection = self._interface.set_peer_connection(sstn_peer)
        sstn_fingerprint = sstn_data['fingerprint']
        self._save_connection(sstn_fingerprint, connection, True)
        self.__send_hello(connection)
        print ('signal client {} send request for swarm to sstn {}'.format(self._interface, connection))

    def __send_hello(self, connection):
        self._interface.send(self.get_fingerprint(), connection)

    def __noop(self, msg, peer):
        return True

    def handle_request(self, msg, connection):
        print ('### SignalClientHandler.handle_request')
        func = self.__define_request_type(msg, connection)
        if func and func(msg, connection) is True:
            return
        self.__external_handle_request(msg, connection)

    def __define_request_type(self, msg, connection):
        if self._msg_is_ping(msg):
            return self.__noop

        if self.__msg_is_peer_list(msg):
            return self.__handle_peer_list

        if self.__msg_is_hello(msg):
            return self.__handle_hello

        return None

    def __msg_is_hello(self, msg):
        return len(msg) == self.fingerprint_length

    def __msg_is_peer_list(self, msg):
        if self.__msg_has_peer_list_length(msg) and \
           self.__get_fingerprint_from_msg(msg) in self._peers:
            return True
        return False

    def __msg_has_peer_list_length(self, msg):
        msg_length = (len(msg) - self.sign_length - self.open_key_length)
        keep_connection_flag_length = msg_length % (self.peer_data_length)
        return keep_connection_flag_length in [0, 1]

    def __get_fingerprint_from_msg(self, msg):
        open_key = msg[self.sign_length: self.sign_length + self.open_key_length]
        return pycrypto.sha256(open_key)

    def __handle_hello(self, msg, connection):
        # check fingeprint from sstn and from hello msg
        # save peer
        return True

    def __handle_peer_list(self, msg, connection):
        if not self.__verify_sign(msg):
            print ('signal client {} bed mesg from sstn {}'.format(self, connection))
            return False

        peers = self.__unpack_peers(msg)
        self.__save_peers(peers)
        self.__handle_connection(msg, connection)
        self.__thread_connect_to_peer(peers)
        return True

    def __save_peers(self, peers):
        for peer in peers:
            if self._interface.peer_itself(peer):
                continue
            settings.add_peer(peer)

    def __peer_involved_in_connection(self, peers):
        if (self._interface.peer_itself(peers[0]) or self._interface.peer_itself(peers[-1])) and \
           len(peers) > 1:
            return True
        return False

    def __peer_for_connection(self, peers):
        if self._interface.peer_itself(peers[0]):
            return peers[-1]
        return peers[0]

    def __thread_connect_to_peer(self, peers):
        if not self.__peer_for_connection(peers):
            return

        peer_to_connect = self.__peer_for_connection(peers)
        self.__shutdoown_recuest_connection_to_peer_thread(peer_to_connect)
        # TODO thread to connect

    def __connect_to_peer(self, peer):
        connection = self._interface.set_peer_connection(peer)
        self.__send_hello(connection)
        # increase attempt counter for peer
        # wait timeout try again
        # if no connection:
        #   do UDP hole pinching
        #   UDP hole pinching can be only if that peer came sstn
        print ('signal client {} try connect to {}'.format(self._interface, connection))

    def __shutdoown_recuest_connection_to_peer_thread(self, peer):
        fingerprint = peer['fingerprint']
        if not fingerprint in self.__connection_threads:
            return
        connection_thread = self.__connection_threads[fingerprint]
        if connection_thread.isAlive():
            connection_thread._tstate_lock = None
            connection_thread._stop()
        del self.__connection_threads[fingerprint]

    def __unpack_peers(self, msg):
        peers = []
        _, msg = self.__cut_data(msg, self.sign_length + self.open_key_length)
        while len(msg) >= (self.ip_length + self.port_length):
            peer_data, msg = self.__cut_data(msg, self.ip_length + self.port_length)
            fingerprint, msg = self.__cut_data(msg, self.fingerprint_length)
            peer = self.__unpack_peer(peer_data)
            peer.update({'fingerprint': fingerprint})
            peers.append(peer)
        return peers

    def __unpack_peer(self, peer_data):
        ip_data, port_data = self.__cut_data(peer_data, self.ip_length)
        ip = self.__unpack_ip(ip_data)
        port = self.__unpack_port(port_data)
        return {'ip': ip, 'port': port}

    def __unpack_ip(self, ip_data):
        ip_list = []
        for octet in ip_data:
            ip_list.append(str(octet))
        return '.'.join(ip_list)

    def __unpack_port(self, port_data):
        return struct.unpack('>H', port_data)[0]

    def __handle_connection(self, msg, connection):
        recived_byte_flag_close_sstn_connection = self.__msg_has_close_connection_flag(msg)
        if recived_byte_flag_close_sstn_connection is False:
            return
        fingerprint = self.__get_fingerprint_from_msg(msg)
        self._remove_peer(fingerprint)

    def __msg_has_close_connection_flag(self, msg):
        msg_length = len(msg) - self.open_key_length - self.sign_length
        return True if msg_length % self.peer_data_length == 1 else False

    def __verify_sign(self, msg):
        sign, tail = self.__cut_data(msg, self.sign_length)
        open_key, signed_msg = self.__cut_data(tail, self.open_key_length)
        ecdsa = pycrypto.ECDSA(pub_key=open_key)
        return ecdsa.check_signature(signed_msg, sign)

    def __cut_data(self, data, length):
        return data[0: length], data[length:]

    def __thread_ping_sstn(self):
        self.__ping_sstn_thread = threading.Thread(target=self.__ping_sstn)
        self.__ping_sstn_thread.start()

    def __ping_sstn(self):
        self._wait_interface_socket()

        while True:
            if len(self._interface.get_connections()) == 0:
                self.__request_swarm_peers()
            self._clean_connections()
            for fingerprint in self._peers:
                connections = self._get_peer_connections(fingerprint)
                for connection in connections:
                    self._interface.ping(connection)
            time.sleep(settings.ping_time)

    def close(self):
        self.__ping_sstn_thread._tstate_lock = None
        self.__ping_sstn_thread._stop()
        print ('sctn close')


if __name__ == "__main__":
    print('start sstn')
    signal_server = host.UDPHost(handler=SignalServerHandler, host='', port=10002)

    try:
        while True:
            time.sleep(5)
    except KeyboardInterrupt:
        signal_server.stop()

    print('stop sstn')
