# -*- coding: utf-8 -*-
import select
import socket
import errno

__author__ = 'Akinava'
__author_email__ = 'akinava@gmail.com'
__copyright__ = "Copyright © 2019"
__license__ = "MIT License"
__version__ = [0, 0]


# TODO
# check fragmentation IP_DONTFRAGMENT


class UDPHost:
    max_connection_by_peer = 2
    max_peers = 200
    buffer_size = 1024

    def __init__(self, host, port, handler):
        self.port = port
        self.host = host
        self.handler = handler(self)
        self.peers = {}  # {peer_id: {'MTU': MTU, 'ip'}}
        #self.connect()

    #def connect(self):
    #    self.poll_hosts_by_list()
    #    self.find_hosts_by_broadcast()
    #    self.call_signal_server()

    #def find_hosts_by_broadcast(self)
    #    self.rise_server()
    #    self.send_broadcast()

    def make_socket(self):
        self.socket = socket.socket(family=socket.AF_INET, type=socket.SOCK_DGRAM)
        #self.socket.listen(self.max_peers)
        #self.socket.setblocking(0)

    def bind_socket(self):
        try:
            self.socket.bind((self.host, self.port))
        except socket.error as e:
            if e.errno == errno.EADDRINUSE:
                print('Error: port {} is already in use'.format(self.port))
                self.port += 1
                self.bind_socket()

    def rize_server(self):
        self.make_socket()
        self.bind_socket()
        #self.epoll = select.epoll()
        #self.epoll.register(self.socket.fileno(), select.EPOLLIN | select.EPOLLET)
        print('Info: run server on {} port'.format(self.port))

        while True:
            #events = epoll.poll(1)

            #for fileno, event in events:
            #    print ('event', fileno, event)




            data, connection = self.socket.recvfrom(self.buffer_size)
            self.handler.handle_request(data, connection)

    #def handle_request(self, data, connection):
    #    if data == b'confurm':
    #        print('Info: get confurm from {}'.format(connection))
    #        return

    #    # FIXME broadcast
    #    if b'Broadcast message.' in data:
    #        host = connection[0]
    #        port = int(data.decode('utf8').split(' ')[-1])
    #        print('Info: add server ({}:{})'.format(host, port))
    #        self.peers.append((host, port))
    #        # send peers info for other nebors
    #        return

    #    self.handler.handle_network_event(connection, data)
    #    self.socket.sendto(b'confurm', connection)

    def __del__(self):
        # save peers list
        #self.epoll.close()
        self.socket.close()

    #def send_broadcast(self):
    #    # FIXME
    #    broadcast_connection = ('255.255.255.255', self.port-1)
    #    broadcast_message = 'Broadcast message. Server in a port {}'.format(self.port)
    #    br_socket = socket.socket(family=socket.AF_INET, type=socket.SOCK_DGRAM)
    #    br_socket.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
    #    br_socket.sendto(broadcast_message.encode('utf8'), broadcast_connection)
    #    br_socket.close()

    def send(self, connection, msg):
        self.socket.sendto(msg, connection)

    def get_fingerprint(self):
        return self.handler.get_fingerprint()

    #def recived(self):
    #    data, addr = self.socket.recvfrom(self.buffer_size)

