# -*- coding: utf-8 -*-
__author__ = 'Akinava'
__author_email__ = 'akinava@gmail.com'
__copyright__ = 'Copyright © 2019'
__license__ = 'MIT License'
__version__ = [0, 0]


from time import time
from crypt_tools import Tools as CryptTools
from utilit import encode
import settings
from settings import logger
from net_pool import NetPool


class Connection:
    def __init__(self, remote_addr=None, transport=None, request=None):
        logger.info('')
        self.__transport = transport
        self.__set_time_received_message()
        if request:
            self.__request = request
        if remote_addr:
            self.__set_remote_addr(remote_addr)
        NetPool().save_connection(self)

    def __str__(self):
        return '{}:{}'.format(self.__remote_host, self.__remote_port)

    def __repr__(self):
        return '{}:{}'.format(self.__remote_host, self.__remote_port)

    def __set_remote_addr(self, addr):
        self.__remote_host, self.__remote_port = addr

    def __eq__(self, connection):
        if self.__remote_host != connection.__remote_host:
            return False
        if self.__remote_port != connection.__remote_port:
            return False
        return True

    def is_alive(self):
        if self.__transport.is_closing():
            return False
        return True

    def last_received_message_is_over_time_out(self):
        return time() - self.__received_message_time > settings.peer_timeout_seconds

    def last_sent_message_is_over_ping_time(self):
        if not hasattr(self, '_sent_message_time'):
            return True
        return time() - self._sent_message_time > settings.peer_ping_time_seconds

    def __set_time_sent_message(self):
        self._sent_message_time = time()

    def __set_time_received_message(self):
        self.__received_message_time = time()

    def set_type(self, connection_type):
        self.type = connection_type

    def get_type(self):
        if hasattr(self, 'type'):
            return self.type
        return None

    def set_request(self, request):
        self.__request = request

    def get_request(self):
        return self.__request

    def set_pub_key(self, pub_key):
        self.__pub_key = pub_key
        self.fingerprint = CryptTools().make_fingerprint(self.__pub_key)

    def get_pub_key(self):
        return self.__pub_key

    def get_fingerprint(self):
        return self.fingerprint

    def __get_remote_addr(self):
        return (self.__remote_host, self.__remote_port)

    def send(self, response):
        logger.info('%s to %s' % (response.hex(), (self.__remote_host, self.__remote_port)))
        self.__transport.sendto(encode(response), self.__get_remote_addr())
        self.__set_time_sent_message()

    def shutdown(self):
        if self.__transport.is_closing():
            return
        self.__transport.close()
