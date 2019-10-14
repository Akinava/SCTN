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
from settings import logger


__author__ = 'Akinava'
__author_email__ = 'akinava@gmail.com'
__copyright__ = "Copyright © 2019"
__license__ = "MIT License"
__version__ = [0, 0]
# Signal Server for Traversal NAT


# TODO handle shutdown thread

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
        logger.info('setup ECDSA, fingerprint {}'.format(
            pycrypto.B58().pack(self.get_fingerprint())))

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
        self._interface.listener_is_ready()

    def get_fingerprint(self):
        open_key = self._ecdsa.get_pub_key()
        fingerprint = pycrypto.sha256(open_key)
        return fingerprint

    def _get_rundom_sstn_peer_from_settings(self):
        if len(settings.peers) == 0:
            return None
        sstn_peer_list = self._get_sstn_list_from_settings()
        if len(sstn_peer_list) == 0:
            return None
        random.shuffle(sstn_peer_list)
        return sstn_peer_list[0]

    def _get_sstn_list_from_settings(self):
        if len(settings.peers) == 0:
            return []
        sstn_peer_list = []
        for fingerprint in settings.peers:
            peer_data = settings.peers[fingerprint].copy()
            if self._interface.peer_itself(peer_data) or \
               not peer_data.get('signal') is True:
                continue
            peer_data['fingerprint'] = fingerprint
            sstn_peer_list.append(peer_data)
        return sstn_peer_list

    def _save_peer(self, fingerprint, connection, signal=False):
        # self._interface.update_time_last_responce(connection)
        if fingerprint not in self._peers:
            self._peers[fingerprint] = {'connections': []}
        if connection not in self._peers[fingerprint]['connections']:
            self._peers[fingerprint]['connections'].append(connection)
        if signal:
            self._peers[fingerprint]['signal'] = True

    def _remove_peer(self, fingerprint):
        connections = self._peers[fingerprint]['connections']
        for connection in connections:
            self._interface.remove_connection(connection)
        if fingerprint in self._peers:
            del self._peers[fingerprint]

    def _get_peer_connections(self, fingerprint):
        return self._peers.get(fingerprint, {}).get('connections', [])

    def _clean_peers_connections(self):
        for fingerprint in self._peers:
            connections = self._get_peer_connections(fingerprint)
            connections_tmp = []
            for connection in connections:
                if connection not in self._interface.get_connections():
                    continue
                connections_tmp.append(connection)
            self._peers[fingerprint]['connections'] = connections_tmp

    def _clean_peers(self):
        fingerprints = list(self._peers)
        for fingerprint in fingerprints:
            connections = self._peers[fingerprint]['connections']
            if len(connections) == 0:
                self._remove_peer(fingerprint)

    def _pack_ip(self, ip):
        ip_data = b''
        for octet in ip.split('.'):
            ip_data += struct.pack('>B', int(octet))
        return ip_data

    def _pack_port(self, port):
        return struct.pack('>H', port)

    def _sign_msg(self, msg):
        sign = self._ecdsa.sign(msg)
        open_key = self._ecdsa.get_pub_key()
        return sign + open_key


class SignalServerHandler(SignalHandler):
    def __init__(self, interface):
        self._setup_ecdsa()
        self._interface = interface
        self._peers = {}
        # request self external port and client
        self.__thread_connect_to_swarm()
        self.__queue = []

    def __thread_connect_to_swarm(self):
        connect_to_swarm_thread = threading.Thread(
            name='connect to swarm',
            target=self.__connect_to_swarm
        )
        connect_to_swarm_thread.start()

    def __connect_to_swarm(self):
        self._wait_interface_socket()
        sstn_peer = self._get_rundom_sstn_peer_from_settings()
        if sstn_peer is None:
            logger.warning('signal server {} no sstn to request a swarm'.format(self._interface._default_listener_port()))
            return

        # TODO
        # connect to sstn
        # request swarm
        # stay or leave
        logger.info('signal server {} connect to swarm is finished'.format(self._interface._default_listener_port()))

    def __pack_peer(self, fingerprint):
        connection = self._peers[fingerprint]['connections'][0]
        return self._pack_ip(connection[host.UDPHost.peer_ip]) + \
            self._pack_port(connection[host.UDPHost.peer_port])

    def handle_request(self, msg, connection):
        if not self.__check_hello(msg):
            logger.info('signal server {} remove peer {} wrong fingerprint'.format(self._interface._default_listener_port(), connection))
            self.__interface.remove_connection(connection)
            return

        self._clean_peers_connections()
        self.__clean_old_connections()
        self._clean_peers()
        self.__clean_queue()

        self._save_peer(msg, connection)
        self.__put_in_queue(msg)
        self.__send_swarm_list()

    def remove_connection(self):
        self._clean_peers_connections()
        self._clean_peers()
        self.__clean_queue()

    def __clean_queue(self):
        tmp_queue = []
        for fingerprint in self.__queue:
            if fingerprint in self._peers:
                tmp_queue.append(fingerprint)
        self.__queue = tmp_queue

    def __clean_old_connections(self):
        old = 0
        for fingerprint in self._peers:
            connections = self._peers[fingerprint]['connections']
            while len(connections) > 1:
                self._interface.remove_connection(connections[old])
                self._peers[fingerprint]['connections'] = connections[1:]

    def __put_in_queue(self, fingerprint):
        if fingerprint in self.__queue:
            self.__queue.remove(fingerprint)
        self.__queue.append(fingerprint)

    def __remove_from_queue(self, fingerprint):
        if fingerprint in self.__queue:
            self.__queue.remove(fingerprint)

    def __check_hello(self, msg):
        return len(msg) == self.fingerprint_length

    def __send_swarm_list(self):
        old = 0
        msg = self.__make_swarm_msg()

        if self.__oversupply_of_peers():
            leave_msg = self.__add_close_connection_flag(msg)
            leave_msg = self._sign_msg(leave_msg) + leave_msg
            leave_peer_fingerprint = self.__queue[old]
            leave_peer_connection = self._get_peer_connections(leave_peer_fingerprint)[old]
            logger.info('signal server {} send swarm (size {} peers) to peer {} and close connect'.format(
                self._interface._default_listener_port(),
                len(self.__queue),
                leave_peer_connection))
            self._interface.send(leave_msg, leave_peer_connection)
            self._remove_peer(leave_peer_fingerprint)
            self.__remove_from_queue(leave_peer_fingerprint)

        msg = self._sign_msg(msg) + msg
        for fingerprint in self.__queue:
            connection = self._get_peer_connections(fingerprint)[old]
            logger.info('signal server {} send swarm (size {} peers) to peer {}'.format(
                self._interface._default_listener_port(),
                len(self.__queue),
                connection))
            self._interface.send(msg, connection)

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

    def close(self):
        logger.info('sstn save the key')
        with open(settings.shadow_file, 'w') as shadow_file:
            priv_key = self._ecdsa.get_priv_key()
            priv_key_b58 = pycrypto.B58().pack(priv_key)
            shadow_file.write(json.dumps({
                'ecdsa': priv_key_b58
            }, indent=2))

    def __del__(self):
        self.close()


class SignalClientHandler(SignalHandler):
    # send sstn peers
    # request new swarm connect from swarm peer
    def __init__(self, interface, external_handler):
        self._ecdsa = pycrypto.ECDSA()    # FIXME ECDSA
        # self._setup_ecdsa()             # FIXME ECDSA
        self._interface = interface
        self._peers = {}                  # {fingerprint: {'signal': True, 'connections': [peer, connection]}}
        self.__handler = external_handler
        self.__reload_external_handler_methods()
        self.__connection_threads = {}
        self.__swarm_watcher()

    def __swarm_watcher(self):
        self.__swarm_maker_thread = threading.Thread(
            name='swarm maker',
            target=self.__swarm_maker
        )
        self.__swarm_maker_thread.start()

    def __swarm_maker(self):
        self._wait_interface_socket()
        while self.__swarm_maker_thread.is_alive():
            if len(self._interface.get_connections()) < settings.min_peer_connections:
                # TODO if peer in swarm request peer connect
                # TODO if swarm peers in settings, connect to them
                self.__call_peers_by_sstn()
            time.sleep(settings.ping_time)

    def __reload_external_handler_methods(self):
        self.__external_handle_request = self.__handler.handle_request
        self.__handler.handle_request = self.handle_request
        self.__handler.is_ready = self.is_ready
        self.__handler.remove_connection = self.remove_connection

    def is_ready(self):
        return self.__peer_has_connection_with_swarm()

    def __peer_has_connection_with_sstn(self):
        for fingerprint in self._peers:
            peer_is_signal = self._peers[fingerprint].get('signal')
            if peer_is_signal:
                return True
        return False

    def __peer_has_connection_with_swarm(self):
        for fingerprint in self._peers:
            peer_is_signal = self._peers[fingerprint].get('signal')
            if not peer_is_signal:
                return True
        return False

    def __call_peers_by_sstn(self):
        if self.__peer_has_connection_with_sstn():
            return
        logger.info('signal client {} request swarm from sstn'.format(
            self._interface._default_listener_port()))
        sstn_peer = self._get_rundom_sstn_peer_from_settings()
        if sstn_peer is None:
            logger.warning('signal client {} no sstn in peers file. Stop the peer'.format(
                self._interface._default_listener_port()))
            self._interface.stop()
            return
        self.__send_hello(sstn_peer)

    def __send_hello(self, peer, listener_port=None):
        fingerprint = peer['fingerprint']
        if listener_port is None:
            connection = self._interface.set_peer_connection(peer)
            listener_port = self._interface._default_listener_port()
        self._save_peer(fingerprint, connection, peer.get('signal', False))
        logger.info('signal client {} send hello to {}'.format(listener_port, connection))
        self._interface.send(self.get_fingerprint(), connection)

    def handle_request(self, msg, connection):
        self._clean_peers_connections()
        self._clean_peers()
        self.__clean_request_connection_to_peer_threads()

        func = self.__define_request_type(msg, connection)
        if func and func(msg, connection) is True:
            return
        self.__external_handle_request(msg, connection)

    def __define_request_type(self, msg, connection):
        if self.__is_msg_swarm_peers_list(msg, connection):
            return self.__handle_swarm_peer_list

        if self.__is_msg_sstn_peer_list(msg, connection):
            return self.__handle_sstn_peer_list

        if self.__is_msg_hello(msg):
            return self.__handle_hello

        return None

    def __is_msg_hello(self, msg):
        return len(msg) == self.fingerprint_length

    def __is_msg_swarm_peers_list(self, msg, connection):
        if not self.__is_msg_peer_list(msg):
            return False
        fingerprint = self.__get_fingerprint_from_msg(msg)
        peer_is_signal = self._peers[fingerprint].get('signal', False)
        return peer_is_signal

    def __is_msg_sstn_peer_list(self, msg, connection):
        if not self.__is_msg_peer_list(msg):
            return False
        fingerprint = self.__get_fingerprint_from_msg(msg)
        peer_is_signal = self._peers[fingerprint].get('signal', False)
        return peer_is_signal is False

    def __is_msg_peer_list(self, msg):
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

    def __handle_hello(self, fingerprint, connection):
        logger.info('signal client {} received hello from {}'.format(self._interface._default_listener_port(), connection))
        self.__exit_from_connection_thread(fingerprint)
        if self.__check_hello_from_itself(fingerprint):
            self._interface.remove_connection(connection)
            return True
        msg = self.__make_sstn_list_msg()
        logger.info('signal client {} send sstn list to {}'.format(self._interface._default_listener_port(), connection))
        self._interface.send(msg, connection)
        return True

    def remove_connection(self):
        self._clean_peers_connections()
        self._clean_peers()

    def __check_hello_from_itself(self, fingerprint):
        return fingerprint == self.get_fingerprint()

    def __make_sstn_list_msg(self):
        msg = b''
        sstn_peers_list = self._get_sstn_list_from_settings()
        for sstn_peer in sstn_peers_list:
            msg += self.__pack_peer(sstn_peer)
            msg += sstn_peer['fingerprint']
        return self._sign_msg(msg) + msg

    def __pack_peer(self, peer):
        return self._pack_ip(peer['ip']) + self._pack_port(peer['port'])

    def __handle_swarm_peer_list(self, msg, connection):
        peers = self.__handle_peer_list(msg)
        if peers is False:
            logger.info('signal client {} bad mesg from swarm peer {}'.format(self._interface._default_listener_port(), connection))
            return False
        self.__save_peers_to_settings(peers)
        logger.info('signal client {} received swarm peers from {} got {} peers'.format(self._interface._default_listener_port(), connection, len(peers)))
        self.__handle_connection(msg, connection)
        self.__thread_connect_to_peer(peers)
        return True

    def __handle_sstn_peer_list(self, msg, connection):
        peers = self.__handle_peer_list(msg)
        if peers is False:
            logger.info('signal client {} bed mesg from sstn {}'.format(self._interface._default_listener_port(), connection))
            return False
        self.__save_sstn_peers(peers)
        logger.info('signal client {} received sstn {} peers from {}'.format(self._interface._default_listener_port(), len(peers), connection))
        fingerprint = self.__get_fingerprint_from_msg(msg)
        self.__exit_from_connection_thread(fingerprint)
        return True

    def __handle_peer_list(self, msg):
        if not self.__verify_sign(msg):
            return False
        return self.__unpack_peers(msg)

    def __save_sstn_peers(self, peers):
        for peer in peers:
            peer.update({'signal': True})
            self.__save_peer_to_settings(peer)

    def __save_peers_to_settings(self, peers):
        for peer in peers:
            self.__save_peer_to_settings(peer)

    def __save_peer_to_settings(self, peer):
        if self._interface.peer_itself(peer):
            return
        settings.add_peer(peer)

    def __peer_itself(self, peer):
        return peer['fingerprint'] == self.get_fingerprint()

    def __peer_involved_in_connection(self, peers):
        if len(peers) > 1 and \
           (self.__peer_itself(peers[0]) or self.__peer_itself(peers[-1])):
            return True

        return False

    def __get_swarm_peer_for_connection(self, peers):
        if self.__peer_itself(peers[0]):
            return peers[-1]
        return peers[0]

    def __thread_connect_to_peer(self, peers):
        if not self.__peer_involved_in_connection(peers):
            return

        peer_to_connect = self.__get_swarm_peer_for_connection(peers)
        fingerprint = peer_to_connect['fingerprint']
        self.__shutdoown_request_thread(fingerprint)
        connect_to_peer_tread = threading.Thread(
            name='connect_to_peer {}'.format(pycrypto.B58().pack(fingerprint)[:6]),
            target=self.__connect_to_peer,
            args=(peer_to_connect,))
        thread_data = {'thread': connect_to_peer_tread, 'alive': True}
        self.__connection_threads[fingerprint] = thread_data
        connect_to_peer_tread.start()

    def __connect_to_peer(self, peer):
        self.__direct_connect(peer)

        if self.__check_connection_is_done(peer):
            self.__shootdown_connection_thread(peer)
            return

        self.__hole_pinching(peer)

    def __hole_pinching(self, peer):
        # TODO probably better approach will be to send request by 10 attempts
        for hole in range(settings.holes):
            src_port = self._interface.rize_listener()
            dst_port_min = peer['port'] + 1
            dst_port_max = peer['port'] + 1 + settings.holes
            for dst_port in range(dst_port_min, dst_port_max):
                print ('pinching to peer {} input port {} to output port {}'.format(peer, src_port, dst_port))

    def __check_connection_is_done(self, peer):
        fingerprint = peer['fingerprint']
        if fingerprint not in self.__connection_threads:
            return True
        return self.__connection_threads[fingerprint]['alive'] is False

    def __shootdown_connection_thread(self, peer):
        fingerprint = peer['fingerprint']
        if fingerprint in self.__connection_threads:
            del self.__connection_threads[fingerprint]

    def __direct_connect(self, peer):
        for attempt in range(settings.attempts_connect_to_peer):
            logger.info('attempt {} connect {} to {} directly'.format(
                attempt,
                self._interface._default_listener_port(),
                (peer['ip'],
                 peer['port'])))
            self.__send_hello(peer)
            time.sleep(settings.ping_time)

            if self.__check_connection_is_done(peer):
                return

    def __exit_from_connection_thread(self, fingerprint):
        if fingerprint not in self.__connection_threads:
            return
        self.__connection_threads[fingerprint]['alive'] = False

    def __clean_request_connection_to_peer_threads(self):
        dead_threads = []
        for fingerprint in self.__connection_threads:
            if fingerprint not in self._peers:
                dead_threads.append(fingerprint)
        for fingerprint in dead_threads:
            self.__exit_from_connection_thread(fingerprint)

    def __shutdoown_request_threads(self):
        threads = list(self.__connection_threads.keys())
        for fingerprint in threads:
            self.__shutdoown_request_thread(fingerprint)

    def __shutdoown_swarm_maker_thread(self):
        self.__swarm_maker_thread._tstate_lock = None
        self.__swarm_maker_thread._stop()

    def __shutdoown_request_thread(self, fingerprint):
        if fingerprint not in self.__connection_threads:
            return

        thread_data = self.__connection_threads[fingerprint]
        thread_data['alive'] = False
        if thread_data['thread'].isAlive():
            thread_data['thread']._tstate_lock = None
            thread_data['thread']._stop()
        self.__remove_connection_thread(fingerprint)

    def __remove_connection_thread(self, fingerprint):
        if fingerprint in self.__connection_threads:
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
        logger.info('signal client {} got close connection flag from {}'.format(self._interface._default_listener_port(), connection))
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

    def close(self):
        self.__shutdoown_swarm_maker_thread()
        self.__shutdoown_request_threads()
        logger.info('sctn close')


if __name__ == "__main__":
    logger.info('start sstn')
    signal_server = host.UDPHost(handler=SignalServerHandler, host='', port=10002)

    try:
        while True:
            time.sleep(5)
    except KeyboardInterrupt:
        signal_server.stop()

    logger.info('stop sstn')
