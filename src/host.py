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

    min_user_port = 0x400
    max_user_port = 0xbfff
    max_port      = 0xffff

    ping_msg      = b''

    def __init__(self, handler, host, port=settings.port):
        self.port = port
        self.host = host
        self.__connections = {}  # {(ip, port, incoming_port): {'MTU': MTU, 'last_response': timestamp}}
        self.__listeners = {}    # {port: {'thread': listener_tread, 'alive': True, 'socket': socket}}
        self.__rize_peer()
        self.__thread_check_connections()
        self.__handler = handler(self)

    def get_connections(self):
        return self.__connections.keys()

    def get_connection_data(self, connection):
        return self.__connections.get(connection)

    def get_connection_last_request_time(self, connection):
        return self.get_connection_data(connection)['last_request']

    def __update_time_last_response(self, connection):
        self.save_connection(connection)
        self.__connections[connection]['last_response'] = time.time()

    def __update_time_last_request(self, connection):
        self.save_connection(connection)
        self.__connections[connection]['last_request'] = time.time()

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
        print ('peer {} run listener on port {}'.format(self._default_listener_port(), listener_port))
        while self.__listeners[listener_port]['alive']:
            sock = self.__listeners[listener_port]['socket']
            msg, peer = sock.recvfrom(settings.buffer_size)
            connection = peer + (listener_port,)
            self.__update_time_last_response(connection)
            if self.__msg_is_ping(msg):
                continue
            self.__handler.handle_request(msg, connection)
        self.__shutdown_listener(listener_port)

    def __msg_is_ping(self, msg):
        return msg == self.ping_msg

    def __thread_check_connections(self):
        self.__check_connections_thread = threading.Thread(target=self.__check_connections)
        self.__check_connections_thread.start()

    def __check_connections(self):
        while True:
            self.__check_alive_connections()
            self.__check_alive_listeners()
            self.__ping_connections()
            time.sleep(settings.ping_time)

    def get_ip(self):
        if not hasattr(self, 'ip'):
            self.ip = socket.gethostbyname(socket.gethostname())
        return self.ip

    def __stop_listeners(self):
        for port in self.__listeners:
            self.__stop_listener(port)

    def __stop_listener(self, port):
        self.__listeners[port]['alive'] = False

    def __shutdown_listeners(self):
        ports = list(self.__listeners)
        for port in ports:
            self.__shutdown_listener(port)

    def __shutdown_listener(self, port):
        self.__listeners[port]['socket'].close()
        self.__listeners[port]['thread']._tstate_lock = None
        self.__listeners[port]['thread']._stop()
        del self.__listeners[port]

    def __shutdown_check_connections(self):
        self.__check_connections_thread._tstate_lock = None
        self.__check_connections_thread._stop()

    def stop(self):
        self.__handler.close()
        self.__shutdown_check_connections()
        self.__shutdown_listeners()
        print ('host stop')

    def __del__(self):
        self.stop()
        # save peers list

    def peer_itself(self, peer):
        if peer['ip'] == self.get_ip() and \
           peer['port'] in self.__listeners:
            return True
        return False

    def _default_listener_port(self):
        return min(self.__listeners)

    def set_peer_connection(self, peer):
        default_tistener_port = self._default_listener_port()
        return (peer['ip'], peer['port'], default_tistener_port)

    def send(self, msg, connection):
        # FIXME if MTU didn't setup use min_UDP_MTU
        if len(msg) > settings.max_UDP_MTU:
            print ('peer {} can\'t send the message with length {}'.format(self._default_listener_port(), len(msg)))

        incoming_port = connection[self.incoming_port]
        peer = (connection[self.peer_ip], connection[self.peer_port])
        # print ('peer {} send a message to {}'.format(self, connection))
        self.__listeners[incoming_port]['socket'].sendto(msg, peer)
        self.__update_time_last_request(connection)

    def __check_alive_listeners(self):
        working_ports = set()
        working_ports.add(self._default_listener_port())
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
            if not self.__check_connection_is_alive(connection):
                dead_connections.append(connection)

        for connection in dead_connections:
            self.remove_connection(connection)

    def __ping_connections(self):
        for connection in self.__connections:
            last_request_time = self.__connections[connection].get('last_request')

            if last_request_time is None or time.time() - last_request_time > settings.ping_time:
                print ('### {} ping {}'.format(self._default_listener_port(), connection))
                self.__ping(connection)

    def __check_connection_is_alive(self, connection):
        last_response_time = self.__connections[connection].get('last_response')
        if last_response_time is None:
            last_request_time = self.__connections[connection]['last_request']
            return time.time() - last_request_time > settings.peer_timeout
        return time.time() - last_response_time < settings.peer_timeout

    def remove_connection(self, connection):
        last_request_time = time.time() - self.__connections[connection]['last_request']
        last_response_time = time.time() - self.__connections[connection]['last_response']
        print ('peer {} remove connection {} last_request_time {} last_response_time {}'.format(
            self._default_listener_port(),
            connection,
            last_request_time, last_response_time))
        if connection in self.__connections:
            del self.__connections[connection]

    def __ping(self, connection):
        self.send(self.ping_msg, connection)
