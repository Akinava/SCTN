# -*- coding: utf-8 -*-
__author__ = 'Akinava'
__author_email__ = 'akinava@gmail.com'
__copyright__ = "Copyright © 2019"
__license__ = "MIT License"
__version__ = [0, 0]


server = {
    'request': 'response',
    'hello': 'swarm_list',
}

client = {
    'request': 'response',
    'swarm_list': None
}


class Handler:
    def __init__(self, protocol, crypt_tools):
        self.__protocol = protocol
        self.__crypt_tools = crypt_tools
        # TODO get fingerprint

    def handle(self, request):
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
            if function_name == 'define_request':
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
        response_name = self.__protocol[request_name]
        response_function_name = 'do_{}'.format(response_name)
        if not hasattr(self, response_function_name):
            return
        return getattr(self, response_function_name)

    def define_ping(self, request):
        if request == '':
            return True
        return False

    def define_hello(self, request):
        # TODO
        pass

    def define_swarm_list(self, request):
        # TODO
        pass

