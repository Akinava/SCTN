# -*- coding: utf-8 -*-
__author__ = 'Akinava'
__author_email__ = 'akinava@gmail.com'
__copyright__ = 'Copyright © 2019'
__license__ = 'MIT License'
__version__ = [0, 0]


import sys
from settings import logger


class GeneralProtocol:
    def connection_made(self, transport):
        logger.info('GeneralProtocol connection_made')
        self.transport = transport

    def datagram_received(self, data, addr):
        logger.info('GeneralProtocol datagram_received')
        request = data.decode()
        response = self.handle(request)
        print('Received %r from %s' % (request, addr))
        print('Send %r to %s' % (response, addr))
        if response is None:
            return
        self.transport.sendto(response.encode(), addr)

    def connection_lost(self, addr):
        logger.info('GeneralProtocol connection_lost')
        pass

    def handle(self, request):
        logger.info('GeneralProtocol handle')
        # TODO make a tread
        request_name = self.define_request(request)
        if request_name is None:
            return
        response_function = self.get_response_function(request_name)
        if response_function is None:
            return
        return response_function(request)

    def define_request(self, request):
        self_functions = dir(self)
        for function_name in self_functions:
            if function_name == sys._getframe().f_code.co_name:
                continue
            if not 'define_' in function_name:
                continue
            define_function = getattr(self, function_name)
            if define_function(request) is False:
                continue
            request_name = function_name.replace('define_', '')
            return request_name
        return None

    def get_response_function(self, request_name):
        response_name = self.protocol[request_name]
        response_function_name = 'do_{}'.format(response_name)
        if not hasattr(self, response_function_name):
            return
        return getattr(self, response_function_name)

    def define_swarm_ping(self, request):
        if request == '':
            return True
        return False

    def define_swarm_hello(self, request):
        # TODO
        pass
