# -*- coding: utf-8 -*-
import socket

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

    def start(self):
        UDPServerSocket = socket.socket(family=socket.AF_INET, type=socket.SOCK_DGRAM)
        UDPServerSocket.bind(('', self.port))
        # make socket
        # send broadcast
        while(True):
            data, addr = UDPServerSocket.recvfrom(self.buffer_size)
            clientMsg = "Message from Client:{}".format(data)
            clientIP  = "Client IP Address:{}".format(addr)
            print(clientMsg)
            print(clientIP)

            # Sending a reply to client
            #UDPServerSocket.sendto(bytesToSend, address)

    def stop(self):
        pass

    def send_broadcast(self):
        pass

    def send(self, msg):
        UDPClientSocket = socket.socket(family=socket.AF_INET, type=socket.SOCK_DGRAM)
        UDPClientSocket.sendto(msg, (self.host, self.port))
        #data = UDPClientSocket.recvfrom(self.buffer_size)
        #msg = "Message from Server {}".format(data[0])

        #print(msg)

