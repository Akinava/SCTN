# -*- coding: utf-8 -*-
__author__ = 'Akinava'
__author_email__ = 'akinava@gmail.com'
__copyright__ = 'Copyright © 2019'
__license__ = 'MIT License'
__version__ = [0, 0]


import pycrypto


class Tools:
    def __init__(self):
        self.get_fingerprint()

    def get_fingerprint(self):
        if self.get_fingerprint_from_file():
            return self.fingerprint
        self.generate_new_fingerprin()
        self.save_fingerprint()

    def get_fingerprint_from_file(self):
        # TODO
        pass

    def generate_new_fingerprin(self):
        # TODO
        pass

    def save_fingerprint(self):
        pass
