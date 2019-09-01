# -*- coding: utf-8 -*-
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
    peer_ip       = 0
    peer_port     = 1
    incoming_port = 2

    min_user_port      = 0x400
    max_user_port = 0xbfff
    max_port      = 0xffff

    def __init__(self, handler, host, port=settings.port):
        self.port = port
        self.host = host
        self.__connections = {}  # {(ip, port, incoming_port): {'MTU': MTU, 'last_response': timestamp}}
        self.__listeners = {}    # {port: {'thread': listener_tread, 'alive': True, 'socket': socket}}
        self.__rize_peer()
        self.__handler = handler(self)

    def get_connections(self):
        return self.__connections.keys()

    def get_connection_data(self, connection):
        return self.__connections.get(connection)

    def get_connection_last_responce_time(self, connection):
        return self.get_connection_data(connection)['last_response']

    def update_connection_timeout(self, connection):
        self.save_connection(connection)
        self.__connections[connection].update({'last_response': time.time()})
        # print('peer {} update timeout with {}'.format(self, connection))

    def save_connection(self, connection):
        if connection not in self.__connections:
            self.__connections[connection] = {}

    def is_ready(self):
        return self.__handler.is_ready()

    def listener_is_ready(self):
        while len(self.__listeners) == 0:
            time.sleep(0.1)

    def __make_socket(self):
        return socket.socket(family=socket.AF_INET, type=socket.SOCK_DGRAM)

    def __bind_socket(self, sock):
        socket_is_bound = False
        port = self.port
        while socket_is_bound is False:
            try:
                sock.bind((self.host, port))
                socket_is_bound = True
                self.__update_listener_data(port, {'socket': sock})
            except socket.error as e:
                if e.errno == errno.EADDRINUSE:
                    print('Error: port {} is already in use'.format(self.port))
                    port += 1
                    if port > self.max_port:
                        port = self.min_user_port
        return port

    def __rize_peer(self):
        port = self.__bind_socket(self.__make_socket())
        self.__start_listener_tread(port)

    def __start_listener_tread(self, listener_port):
        listener_tread = threading.Thread(
            name=self.port,
            target=self.__listener,
            args=(listener_port,))
        self.__update_listener_data(
            listener_port,
            {'thread': listener_tread, 'alive': True})
        listener_tread.start()

    def __update_listener_data(self, port, data):
        if port not in self.__listeners:
            self.__listeners[port] = {}
        self.__listeners[port].update(data)

    def __listener(self, listener_port):
        print ('peer {} run listener on port {}'.format(self, listener_port))
        while self.__listeners[listener_port]['alive']:
            sock = self.__listeners[listener_port]['socket']
            msg, peer = sock.recvfrom(settings.buffer_size)
            connection = peer + (listener_port,)
            self.update_connection_timeout(connection)
            self.__handler.handle_request(msg, connection)
            # TODO __check_alive_connections __check_alive_listeners relocate
            # in to thread
            self.__check_alive_connections()
            self.__check_alive_listeners()

    def get_ip(self):
        if not hasattr(self, 'ip'):
            self.ip = socket.gethostbyname(socket.gethostname())
        return self.ip

    def __stop_listeners(self):
        for port in self.__listeners:
            self.__stop_listener(port)

    def __stop_listener(self, port):
        self.__listeners[port]['alive'] = False
        self.__listeners[port]['socket'].close()
        self.__listeners[port]['thread']._tstate_lock = None
        self.__listeners[port]['thread']._stop()
        del self.__listeners[port]['thread']


    def stop(self):
        self.__handler.close()
        self.__stop_listeners()
        print ('host stop')

    def __del__(self):
        self.stop()
        # save peers list

    def peer_itself(self, peer):
        if peer['ip'] == self.get_ip() and \
           peer['port'] in self.__listeners:
            return True
        return False

    def set_peer_connection(self, peer):
        default_tistener_port = min(self.__listeners)
        return (peer['ip'], peer['port'], default_tistener_port)

    def send(self, msg, connection):
        if len(msg) > settings.max_UDP_MTU:
            print ('peer {} can\'t send the message with length {}'.format(self, len(msg)))

        incoming_port = connection[self.incoming_port]
        peer = (connection[self.peer_ip], connection[self.peer_port])
        # print ('peer {} send a message to {}'.format(self, connection))
        self.__listeners[incoming_port]['socket'].sendto(msg, peer)

    def __check_alive_listeners(self):
        working_ports = set()
        for connection in self.__connections:
            working_ports.add(connection[self.incoming_port])

        for port in self.__listeners:
            if port not in working_ports:
                self.__stop_listener(port)

    # FIXME could be this function needed only for test
    def get_fingerprint(self):
        return self.__handler.get_fingerprint()

    def __check_alive_connections(self):
        dead_connections = []

        for connection in self.__connections:
            if self.__check_if_connection_is_dead(connection):
                print('peer {} remove connection {} by timeout'.format(self, connection))
                dead_connections.append(connection)

        for connection in dead_connections:
            print('peer {} remove dead connection {} from list'.format(self, connection))
            del self.__connections[connection]

        # TODO shutdown listener_tread that are not used
        # print('peer {} has live peers'.format(self.port), self.peers)

    def __check_if_connection_is_dead(self, connection):
        connection_last_action_time = self.__connections[connection]['last_response']
        return time.time() - connection_last_action_time > settings.peer_timeout

    def remove_connection(self, connection):
        print ('peer {} remove connection {}'.format(self.get_port(), connection))
        del self.peers[connection]

    def ping(self, connection):
        self.send(b'', connection)
