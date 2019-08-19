#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import host
import pycrypto

__author__ = 'Akinava'
__author_email__ = 'akinava@gmail.com'
__copyright__ = "Copyright © 2019"
__license__ = "MIT License"
__version__ = [0, 0]


class SignalServerHandler:
    def __init__(self, interface):
        # FIXME setup acdsa if it doesn't exist
        self.ecdsa = pycrypto.ECDSA()
        self.interface = interface
        self.connect_with_sstn()

    def connect_with_sstn(self):


    def handle_request(self, data, connection):
        pass

    # FIXME could be this function needed only for test
    def get_fingerprint(self):
        pub_key = self.ecdsa.get_pub_key()
        fingerprint = pycrypto.sha256(pub_key)
        return fingerprint

    def __del__(self):
        pass
        # save sstn list


# Signal Server for Traversal NAT
