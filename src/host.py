# -*- coding: utf-8 -*-
import socket
import errno

__author__ = 'Akinava'
__author_email__ = 'akinava@gmail.com'
__copyright__ = "Copyright © 2019"
__license__ = "MIT License"
__version__ = [0, 0]


class UDPHost:
    def __init__(self, host, port, handler):
        self.port = port
        self.host = host
        self.handler = handler
        self.peers = []
        self.buffer_size = 1024
        self.make_socket()

    def make_socket(self):
        self.socket = socket.socket(family=socket.AF_INET, type=socket.SOCK_DGRAM)

    def bind_socket(self):
        try:
            self.socket.bind((self.host, self.port))
        except socket.error as e:
            if e.errno == errno.EADDRINUSE:
                print('Error: port {} is already in use'.format(self.port))
                self.port += 1
                self.bind_socket()

    def start(self):
        # TODO check peers list
        self.bind_socket()
        print('Info: run server on {} port'.format(self.port))

        # FIXME broadcast
        self.send_broadcast()

        while True:
            data, connection = self.socket.recvfrom(self.buffer_size)
            self.handle_request(data, connection)

    def handle_request(self, data, connection):
        if data == b'confurm':
            print('Info: get confurm from {}'.format(connection))
            return

        # FIXME broadcast
        if b'Broadcast message.' in data:
            host = connection[0]
            port = int(data.decode('utf8').split(' ')[-1])
            print('Info: add server ({}:{})'.format(host, port))
            self.peers.append((host, port))
            # send peers info for other nebors
            return

        self.handler(connection, data).handle()
        self.socket.sendto(b'confurm', connection)

    def __del__(self):
        # save peers list
        self.socket.close()

    def send_broadcast(self):
        broadcast_connection = ('255.255.255.255', self.port-1)
        broadcast_message = 'Broadcast message. Server in a port {}'.format(self.port)
        br_socket = socket.socket(family=socket.AF_INET, type=socket.SOCK_DGRAM)
        br_socket.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
        br_socket.sendto(broadcast_message.encode('utf8'), broadcast_connection)
        br_socket.close()

    def send(self, connection, msg):
        self.socket.sendto(msg, connection)

    def recived(self):
        data, addr = self.socket.recvfrom(self.buffer_size)

